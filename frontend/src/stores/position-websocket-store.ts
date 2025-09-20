import type { PositionEvent } from "@/lib/types/events/position-event";
import { create } from "zustand";

interface PositionWebsocketState {
  connect: (versionId: string, token: string) => void;
  disconnect: () => void;
  eventsIterator: () => AsyncIterable<PositionEvent>;
}

export const usePositionWebsocketStore = create<PositionWebsocketState>(() => {
  let obj = {} as { ws: WebSocket | null };
  let queue: PositionEvent[] = [];
  let resolveNext: ((value: IteratorResult<PositionEvent>) => void) | null =
    null;

  return {
    connect: (versionId: string, token: string) => {
      if (obj.ws) return;

      const ws = (obj.ws = new WebSocket(
        `${import.meta.env.VITE_WS_BASE_URL}/strategies/versions/${versionId}/positions`,
      ));

      obj.ws = ws;

      ws.onopen = async () => {
        while (ws?.CONNECTING) {
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
        ws!.send(JSON.stringify({ token }));
      };

      ws.onmessage = (ev) => {
        const event: PositionEvent = JSON.parse(ev.data);

        if (resolveNext) {
          resolveNext({ value: event, done: false });
          resolveNext = null;
        } else {
          queue.push(event);
        }
      };

      ws.onclose = () => {
        if (resolveNext) resolveNext({ value: undefined as any, done: true });
        obj.ws = null;
      };
    },

    disconnect: () => {
      if (obj.ws) {
        obj.ws.close();
        obj.ws = null;
      }
    },

    eventsIterator: () => {
      return {
        async *[Symbol.asyncIterator]() {
          while (true) {
            if (queue.length > 0) {
              yield queue.shift()!;
            } else {
              const pos = await new Promise<PositionEvent>((resolve) => {
                resolveNext = (result) => resolve(result.value);
              });

              if (pos === undefined) break;

              yield pos;
            }
          }
        },
      };
    },
  };
});
