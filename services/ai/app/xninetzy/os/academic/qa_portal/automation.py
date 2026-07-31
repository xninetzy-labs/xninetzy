from __future__ import annotations

import asyncio
import base64

from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
    resolve_campus_credentials,
)

QA_RECAPTCHA_SITEKEY = "6LcGZucUAAAAAPCmfQIcBF-3UyXZ5vPOjEqP0ecG"

QA_LOGIN_URL = "https://qa.unair.ac.id/qa/gate/login"
QA_DASHBOARD_URL = (
    "https://qa.unair.ac.id/qa/kuesioner/set_responden_as/"
    "TTAwMS9NYWhhc2lzd2EgUzEvMzMvUzEgLSBTaXN0ZW0gSW5mb3JtYXNp"
)

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
]

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class QaPortalError(RuntimeError):
    pass


def score_to_value(score: int) -> str:
    return str(124 + score)


async def _launch(playwright):
    browser = await playwright.chromium.launch(
        channel="chrome", headless=True, args=BROWSER_ARGS
    )
    context = await browser.new_context(
        viewport={"width": 1366, "height": 900},
        locale="id-ID",
        timezone_id="Asia/Jakarta",
        user_agent=USER_AGENT,
    )
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    page = await context.new_page()
    page.on("dialog", lambda dialog: asyncio.ensure_future(dialog.accept()))
    return browser, context, page


async def _goto_retry(page, url: str, tries: int = 3) -> None:
    for attempt in range(tries):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            return
        except Exception:
            if attempt < tries - 1:
                await asyncio.sleep(10)
    raise QaPortalError(f"Gagal memuat halaman: {url}")


async def _fill_login_fields(page, creds) -> None:
    await page.fill("input[name='userid']", creds.username)
    await page.fill("input[name='password']", creds.password.get_secret_value())
    await page.wait_for_timeout(3000)


async def _fresh_captcha_token(page) -> None:
    for _ in range(10):
        try:
            ok = await page.evaluate(
                """async (sitekey) => {
                    if (typeof grecaptcha === 'undefined' || !grecaptcha.execute) {
                        return false;
                    }
                    const token = await grecaptcha.execute(sitekey, {
                        action: 'validate_captcha',
                    });
                    const el = document.getElementById('g-recaptcha-response');
                    if (el && token) {
                        el.value = token;
                        return true;
                    }
                    return false;
                }""",
                QA_RECAPTCHA_SITEKEY,
            )
        except Exception:
            ok = False
        if ok:
            await page.evaluate(
                "(v) => { const f = document.querySelector('form input[name=action]'); if (f) f.value = v; }",
                "login",
            )
            return
        await page.wait_for_timeout(1000)


async def login(page) -> None:
    creds = resolve_campus_credentials("hebat")
    await _goto_retry(page, QA_LOGIN_URL)
    await page.wait_for_selector("input[name='userid']", timeout=20000)
    for _ in range(6):
        await _fill_login_fields(page, creds)
        await _fresh_captcha_token(page)
        await page.click("button[name='login']")
        await page.wait_for_timeout(6500)
        if "/qa/gate/menu" in page.url:
            return
        await page.wait_for_selector("input[name='userid']", timeout=20000)
    raise QaPortalError("Login QA gagal: tidak sampai ke halaman menu.")


async def open_dashboard(page) -> None:
    await _goto_retry(page, QA_DASHBOARD_URL)
    await page.wait_for_timeout(3000)


async def questionnaire_entries(page) -> list[dict]:
    links = await page.evaluate(
        "[...document.querySelectorAll('a')].map(a => ({t:(a.innerText||'').trim(), h:a.href}))"
    )
    seen = set()
    entries = []
    for link in links:
        if "/qa/kuesioner/form/edit/" not in link["h"]:
            continue
        if link["h"] in seen:
            continue
        seen.add(link["h"])
        code = ""
        try:
            encoded = link["h"].rsplit("/", 1)[-1]
            decoded = base64.b64decode(encoded + "==").decode("utf-8", "ignore")
            code = decoded.split("/")[0]
        except Exception:
            pass
        title = link["t"].splitlines()[0] if link["t"] else ""
        entries.append({"code": code, "title": title, "url": link["h"]})
    return entries


async def list_questionnaires() -> list[dict]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser, context, page = await _launch(playwright)
        try:
            await login(page)
            await open_dashboard(page)
            return await questionnaire_entries(page)
        finally:
            await context.close()
            await browser.close()


async def _fill_radios(page, target_value: str) -> int:
    names = set()
    for _ in range(10):
        names = set(
            await page.evaluate(
                "[...document.querySelectorAll('input[type=radio]')].map(r => r.name)"
            )
        )
        if names:
            break
        await page.wait_for_timeout(1000)
    if not names:
        return 0
    filled = 0
    for name in names:
        options = await page.evaluate(
            "(name) => [...document.querySelectorAll(`input[name='${name}']`)].map(r => r.value)",
            name,
        )
        chosen = target_value if target_value in options else max(options)
        await page.check(f"input[name='{name}'][value='{chosen}']")
        filled += 1
    return filled


async def _submit(page) -> None:
    button = page.locator("button:has-text('Simpan')").first
    if await button.count() > 0:
        await button.click()
    else:
        await page.evaluate("document.querySelector('form')?.requestSubmit()")
    await page.wait_for_timeout(6000)


async def _fill_form_sections(page, target_value: str) -> dict:
    summary = {"sections": [], "total_filled": 0}
    form_url = page.url
    submitted_values = set()
    for _ in range(30):
        mk = page.locator("select#idmk")
        mk_count = await mk.locator("option").count()
        unit = page.locator("select#idunit")
        unit_count = await unit.locator("option").count()
        if mk_count <= 1 and unit_count <= 1:
            if await page.locator("select[required]").count() == 0:
                filled = await _fill_radios(page, target_value)
                if filled:
                    required_text = page.locator("textarea[required]")
                    if await required_text.count() > 0:
                        await required_text.first.fill("Baik")
                    try:
                        await _submit(page)
                    except Exception as exc:
                        summary["sections"].append(
                            {"name": "single", "filled": filled, "error": str(exc)}
                        )
                        return summary
                    summary["sections"].append({"name": "single", "filled": filled})
                    summary["total_filled"] += filled
            break
        if mk_count > 1:
            selector = mk
            select_id = "idmk"
        else:
            selector = unit
            select_id = "idunit"
        option_count = await selector.locator("option").count()
        progressed = False
        for index in range(1, option_count):
            value = await selector.locator("option").nth(index).get_attribute("value")
            label = await selector.locator("option").nth(index).inner_text()
            if value in submitted_values:
                continue
            await selector.select_option(index=index)
            await page.wait_for_timeout(2000)
            if select_id == "idmk":
                dosen = page.locator("select#dosen")
                dosen_count = await dosen.locator("option").count()
                if dosen_count <= 1:
                    summary["sections"].append(
                        {"name": label, "filled": 0, "note": "no dosen"}
                    )
                    continue
                await dosen.select_option(index=1)
                await page.wait_for_timeout(1000)
            filled = await _fill_radios(page, target_value)
            if filled == 0:
                summary["sections"].append(
                    {"name": label, "filled": 0, "note": "no radios"}
                )
                continue
            required_text = page.locator("textarea[required]")
            if await required_text.count() > 0:
                await required_text.first.fill("Baik")
            try:
                await _submit(page)
            except Exception as exc:
                summary["sections"].append(
                    {"name": label, "filled": filled, "error": str(exc)}
                )
                continue
            summary["sections"].append({"name": label, "filled": filled})
            summary["total_filled"] += filled
            progressed = True
            submitted_values.add(value)
            await page.wait_for_timeout(2000)
            if "/qa/kuesioner/success/" in page.url:
                break
        if not progressed:
            break
        await _goto_retry(page, form_url)
        await page.wait_for_timeout(3000)
    return summary


async def fill_all_questionnaires(score: int = 10) -> dict:
    from playwright.async_api import async_playwright

    target_value = score_to_value(score)
    async with async_playwright() as playwright:
        browser = None
        context = None
        page = None
        for attempt in range(1, 4):
            try:
                browser, context, page = await _launch(playwright)
                await login(page)
                break
            except QaPortalError:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
                browser = None
                context = None
                page = None
                if attempt < 3:
                    await asyncio.sleep(15)
        if page is None:
            raise QaPortalError("Login QA gagal setelah 3 percobaan.")
        try:
            await open_dashboard(page)
            entries = await questionnaire_entries(page)
            period = "20252"
            for entry in entries:
                try:
                    encoded = entry["url"].rsplit("/", 1)[-1]
                    decoded = base64.b64decode(encoded + "==").decode("utf-8", "ignore")
                    parts = decoded.split("/")
                    if len(parts) == 2 and parts[1]:
                        period = parts[1]
                        break
                except Exception:
                    pass
            seen_codes = {entry["code"] for entry in entries}
            canonical = [
                ("Q4", "KINERJA TIM DOSEN DALAM PERKULIAHAN (Jenjang Sarjana & Diploma)"),
                ("Q6", "KINERJA TENAGA ADMINISTRASI DEPARTEMEN"),
                ("Q18", "KINERJA SUB BAGIAN FAKULTAS"),
            ]
            for code, title in canonical:
                if code in seen_codes:
                    continue
                encoded = (
                    base64.urlsafe_b64encode(f"{code}/{period}".encode())
                    .decode()
                    .rstrip("=")
                )
                entries.append(
                    {
                        "code": code,
                        "title": title,
                        "url": (
                            "https://qa.unair.ac.id/qa/kuesioner/form/edit/"
                            f"{encoded}"
                        ),
                    }
                )
            results = []
            for entry in entries:
                print(f"[STEP] opening {entry['code']} {entry['title']}")
                await page.goto(entry["url"], wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000)
                try:
                    summary = await _fill_form_sections(page, target_value)
                except Exception as exc:
                    summary = {"error": str(exc)}
                results.append({"code": entry["code"], "title": entry["title"], **summary})
                print(f"[STEP] {entry['code']} done: {summary}")
            await open_dashboard(page)
            body = await page.evaluate("document.body.innerText.slice(0, 3000)")
            return {"score": score, "results": results, "dashboard_text": body}
        finally:
            await context.close()
            await browser.close()
