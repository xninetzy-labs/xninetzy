export function normalizeDigits(value?: string | null): string {
  if (!value) return "";
  return value.replace(/\D/g, "");
}

export function stripDeviceSuffix(jid?: string | null): string {
  if (!jid) return "";
  const [user, server] = jid.split("@");
  const cleanUser = user.split(":")[0];
  return server ? `${cleanUser}@${server}` : cleanUser;
}

export function getJidNumber(jid?: string | null): string {
  if (!jid) return "";
  const user = jid.split("@")[0]?.split(":")[0] || "";
  return normalizeDigits(user);
}

export function isSameWaIdentity(a?: string | null, b?: string | null): boolean {
  const numA = getJidNumber(a);
  const numB = getJidNumber(b);

  if (!numA || !numB) return false;
  if (numA === numB) return true;

  if (numA.length >= 8 && numB.length >= 8) {
    return numA.endsWith(numB.slice(-8)) || numB.endsWith(numA.slice(-8));
  }

  return false;
}

export function getBotIdentity(sock?: { user?: { id?: string; lid?: string } }): {
  rawJid: string;
  jid: string;
  lid?: string;
  number: string;
  mentionText: string;
} {
  const rawJid = sock?.user?.id || "";
  const rawLid = sock?.user?.lid || "";
  const jid = stripDeviceSuffix(rawJid);
  const lid = rawLid ? stripDeviceSuffix(rawLid) : undefined;
  const number = getJidNumber(rawJid);

  return {
    rawJid,
    jid,
    lid,
    number,
    mentionText: number ? `@${number}` : "",
  };
}
