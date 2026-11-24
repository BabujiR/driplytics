/** Theme (light/dark/system) and density, kept in localStorage and applied before first paint. */

export type ThemeChoice = "light" | "dark" | "system";
export type Density = "comfortable" | "compact";

export const THEME_KEY = "dl-theme";
export const DENSITY_KEY = "dl-density";

/** Inline <head> script: sets data-theme / data-density on <html> before the page paints (no flash). */
export const themeInitScript = `(function(){try{var d=document.documentElement,t=localStorage.getItem("${THEME_KEY}")||"system";
d.dataset.theme=t==="dark"||(t==="system"&&matchMedia("(prefers-color-scheme: dark)").matches)?"dark":"light";
d.dataset.density=localStorage.getItem("${DENSITY_KEY}")==="compact"?"compact":"comfortable";}catch(e){}})();`;

export function applyTheme(choice: ThemeChoice): void {
  const dark = choice === "dark" || (choice === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  localStorage.setItem(THEME_KEY, choice);
}

export function applyDensity(density: Density): void {
  document.documentElement.dataset.density = density;
  localStorage.setItem(DENSITY_KEY, density);
}

export function storedTheme(): ThemeChoice {
  const v = localStorage.getItem(THEME_KEY);
  return v === "light" || v === "dark" ? v : "system";
}

export function storedDensity(): Density {
  return localStorage.getItem(DENSITY_KEY) === "compact" ? "compact" : "comfortable";
}
