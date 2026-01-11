export const requireEnv = (name: string) => {
  const value = process.env[name];
  if (value === undefined || value.trim() === '') {
    throw new Error(`${name} is not set`);
  }
  return value;
};
