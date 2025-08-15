const UID = "cr_user_id";
const NAME = "cr_display_name";
const AGE = "cr_age_ok";
const ONB = "cr_onboarding";

export type Onboarding = {
  spirit?: string[];
  tags?: string[];
  season?: string[];
  avoid_tags?: string[];
};

export const getUserId = () => localStorage.getItem(UID) || "";
export const setUserId = (id: string) => localStorage.setItem(UID, id);

export const getDisplayName = () => localStorage.getItem(NAME) || "";
export const setDisplayName = (name: string) => localStorage.setItem(NAME, name);

export const getAgeOk = () => localStorage.getItem(AGE) === "true";
export const setAgeOk = (v: boolean) => localStorage.setItem(AGE, String(v));

export const getOnboarding = (): Onboarding | null => {
  const s = localStorage.getItem(ONB);
  return s ? (JSON.parse(s) as Onboarding) : null;
};
export const setOnboarding = (o: Onboarding) => localStorage.setItem(ONB, JSON.stringify(o));
