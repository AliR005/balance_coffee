import { useQuery } from "@tanstack/react-query";
import {
  getGetMenuLocationsLocationIdMenuGetUrl,
  getListLocationsLocationsGetUrl,
  type LocationOut,
  type MenuOut,
} from "../../shared/api/generated/api";
import { apiGet } from "../../shared/api/base";

/** Точки; признак «открыта сейчас» считает сервер. */
export function useLocations() {
  return useQuery({
    queryKey: ["locations"],
    queryFn: () => apiGet<LocationOut[]>(getListLocationsLocationsGetUrl()),
  });
}

/** Меню точки: категории → продукты → группы → опции. */
export function useMenu(locationId: number | null) {
  return useQuery({
    queryKey: ["menu", locationId],
    queryFn: () => apiGet<MenuOut>(getGetMenuLocationsLocationIdMenuGetUrl(locationId ?? 0)),
    enabled: locationId !== null,
  });
}
