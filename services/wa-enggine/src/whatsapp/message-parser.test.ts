import assert from "node:assert/strict";
import test from "node:test";

import {
  extractMessageText,
  resolveCaptchaReply,
  resolveGradeTokenReply,
} from "./message-parser";

test("button reply uses command id instead of display label", () => {
  const text = extractMessageText({
    buttonsResponseMessage: {
      selectedButtonId: "/approve 42",
      selectedDisplayText: "Approve",
    },
  });

  assert.equal(text, "/approve 42");
});

test("template reply uses command id instead of display label", () => {
  const text = extractMessageText({
    templateButtonReplyMessage: {
      selectedId: "/reject 42",
      selectedDisplayText: "Reject",
    },
  });

  assert.equal(text, "/reject 42");
});

test("plain answer replying to captcha image becomes a bound captcha command", () => {
  const message = {
    extendedTextMessage: {
      text: "Jawabannya 27",
      contextInfo: {
        quotedMessage: {
          imageMessage: {
            caption:
              "Login Cyber Campus\n\nBalas: /captcha challenge_123 JAWABAN",
          },
        },
      },
    },
  };

  assert.equal(
    resolveCaptchaReply("Jawabannya 27", message),
    "/captcha challenge_123 27",
  );
});

test("unrelated reply remains unchanged", () => {
  assert.equal(
    resolveCaptchaReply("27", {
      extendedTextMessage: {
        text: "27",
        contextInfo: {
          quotedMessage: { conversation: "Pesan biasa" },
        },
      },
    }),
    "27",
  );
});

test("captcha reply resolves quoted caption from message cache fallback", () => {
  assert.equal(
    resolveCaptchaReply(
      "Jawabannya A9Z2",
      {
        extendedTextMessage: {
          text: "Jawabannya A9Z2",
          contextInfo: {
            stanzaId: "outbound-captcha",
          },
        },
      },
      {
        imageMessage: {
          caption:
            "Login Cyber Campus\n\nBalas: /captcha challenge_cached JAWABAN",
        },
      },
    ),
    "/captcha challenge_cached A9Z2",
  );
});

test("common catchpa typo is normalized without using the LLM", () => {
  assert.equal(
    resolveCaptchaReply("/catchpa challenge_123 A9Z2"),
    "/captcha challenge_123 A9Z2",
  );
});

test("plain reply to verified token request becomes a bound private command", () => {
  const message = {
    extendedTextMessage: {
      text: "12345",
      contextInfo: {
        quotedMessage: {
          conversation:
            "Verified Token Cyber Campus\n/grade-token grade_123 TOKEN",
        },
      },
    },
  };

  assert.equal(
    resolveGradeTokenReply("12345", message),
    "/grade-token grade_123 12345",
  );
});

test("grade token reply can resolve an outbound text from message cache", () => {
  assert.equal(
    resolveGradeTokenReply(
      "Tokennya 54321",
      {
        extendedTextMessage: {
          text: "Tokennya 54321",
          contextInfo: { stanzaId: "outbound-grade-token" },
        },
      },
      {
        conversation:
          "Verified Token Cyber Campus\n/grade-token grade_cached TOKEN",
      },
    ),
    "/grade-token grade_cached 54321",
  );
});

test("unbound numeric message is not treated as a grade token", () => {
  assert.equal(resolveGradeTokenReply("12345"), "12345");
});
