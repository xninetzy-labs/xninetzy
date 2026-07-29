type LidMappingSocket = {
  signalRepository: {
    lidMapping: {
      getPNForLID(jid: string): Promise<string | null>;
    };
  };
};

export async function resolveCanonicalJid(
  sock: LidMappingSocket,
  jid: string,
): Promise<string> {
  if (!jid.endsWith("@lid")) return jid;

  try {
    return (await sock.signalRepository.lidMapping.getPNForLID(jid)) || jid;
  } catch {
    return jid;
  }
}
