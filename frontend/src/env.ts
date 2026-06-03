export const env = {
  get appId() {
    const id = process.env.NEXT_PUBLIC_SPATIUS_APP_ID;
    if (!id) {
      throw new Error("Missing NEXT_PUBLIC_SPATIUS_APP_ID environment variable.");
    }
    return id;
  },
  get avatarId() {
    const id = process.env.NEXT_PUBLIC_SPATIUS_AVATAR_ID;
    if (!id) {
      throw new Error("Missing NEXT_PUBLIC_SPATIUS_AVATAR_ID environment variable.");
    }
    return id;
  }
};
