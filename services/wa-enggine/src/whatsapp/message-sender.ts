import type { WASocket, WAMessage } from "@whiskeysockets/baileys";

export async function sendTextMessage(
  sock: WASocket,
  jid: string,
  text: string,
  options?: { quoted?: WAMessage }
): Promise<WAMessage | undefined> {
  return sock.sendMessage(jid, { text }, options?.quoted ? { quoted: options.quoted } : undefined);
}
