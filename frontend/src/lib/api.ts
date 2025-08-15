import { API_BASE } from "./config";
import type { Drink, DrinkCard, RecsResponse, SearchResponse, ProfileResponse, FacetsResponse } from "./types";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.url} → ${r.status}`);
  return r.json() as Promise<T>;
}

export async function getFacets(): Promise<FacetsResponse> {
  return j(await fetch(`${API_BASE}/facets`));
}

export async function getDrinks(params: Record<string, string | number | undefined>): Promise<SearchResponse> {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && usp.set(k, String(v)));
  return j(await fetch(`${API_BASE}/drinks?${usp.toString()}`));
}

export async function search(params: Record<string, string | number | undefined>): Promise<SearchResponse> {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && usp.set(k, String(v)));
  return j(await fetch(`${API_BASE}/search?${usp.toString()}`));
}

export async function getDrink(id: string): Promise<Drink> {
  return j(await fetch(`${API_BASE}/drinks/${id}`));
}

export async function getSimilar(id: string, k = 12): Promise<{ items: DrinkCard[]; source: Drink }> {
  return j(await fetch(`${API_BASE}/similar/${id}?k=${k}`));
}

export async function postRecs(body: unknown): Promise<RecsResponse> {
  return j(await fetch(`${API_BASE}/recs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }));
}

export async function postRating(evt: { user_id: string; drink_id: string; rating: number; tried?: boolean }): Promise<any> {
  return j(await fetch(`${API_BASE}/ratings`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(evt) }));
}

export async function getProfile(user_id: string): Promise<ProfileResponse> {
  return j(await fetch(`${API_BASE}/profile?user_id=${encodeURIComponent(user_id)}`));
}
