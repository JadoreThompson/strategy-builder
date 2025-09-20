import type { PositionResponse } from "@/openapi";

export interface PositionEvent {
  type: "new" | "update";
  version_id: string;
  position: PositionResponse;
}
