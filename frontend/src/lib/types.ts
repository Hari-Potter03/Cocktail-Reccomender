export type TasteProfile = Record<string, number>;

export type Drink = {
  id: string;
  name: string;
  image_url?: string;
  primary_spirit?: string | null;
  tags?: string[];
  season?: string[];
  technique?: string | null;
  glass?: string | null;
  ingredients?: string[];
  taste_profile?: TasteProfile;
};

export type DrinkCard = Pick<Drink, "id" | "name" | "image_url" | "primary_spirit" | "tags" | "season"> & {
  reason?: string[];
};

export type SearchResponse = { items: DrinkCard[]; total: number; page: number };
export type RecsResponse = { items: DrinkCard[] };
export type ProfileResponse = {
  user_id: string;
  ratings_count: number;
  has_taste: boolean;
  summary?: { primary_spirit?: string | null; top_tags?: string[]; top_seasons?: string[] };
};
export type FacetsResponse = {
  spirits: Record<string, number>;
  tags: Record<string, number>;
  seasons: Record<string, number>;
  total: number;
};
