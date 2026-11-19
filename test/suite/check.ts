export async function check(
  name: string,
  verify: () => void | Promise<void>,
): Promise<void> {
  try {
    await verify();
    console.log(`PASS: ${name}`);
  } catch (cause) {
    throw new Error(`FAIL: ${name}`, { cause });
  }
}
