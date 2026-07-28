const chatTails = new Map<string, Promise<void>>();

export function runInChatQueue<T>(chatId: string, task: () => Promise<T>): Promise<T> {
  const previous = chatTails.get(chatId) ?? Promise.resolve();
  const run = previous.then(task, task);
  const tail = run.then(
    () => undefined,
    () => undefined,
  );
  chatTails.set(chatId, tail);
  void tail.finally(() => {
    if (chatTails.get(chatId) === tail) chatTails.delete(chatId);
  });
  return run;
}
