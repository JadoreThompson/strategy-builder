import type { TaskStatus } from "@/openapi";
import type { FC } from "react";

const BacktestBadge: FC<{ status: TaskStatus; className: string }> = ({
  status,
  className = "",
}) => {
  const getIconColor = (status: TaskStatus) => {
    switch (status) {
      case "not_started":
        return "bg-gray-200/50 text-gray-500";
      case "pending":
        return "bg-orange-200/50 text-orange-500";
      case "completed":
        return "bg-green-200/50 text-green-500";
      case "failed":
        return "bg-red-200/50 text-red-500";
      default:
        return "bg-gray-200/50 text-gray-500";
    }
  };

  return (
    <span className={`${getIconColor(status)} ${className}`}>
      Backtest{"    "}
      {(() => {
        const s = status.toString();

        if (s.includes("_")) {
          const v = s
            .split("_")
            .map((_s) => _s.charAt(0).toUpperCase() + _s.slice(1))
            .join(" ");
          return v;
        }

        return s.charAt(0).toUpperCase() + s.slice(1);
      })()}
    </span>
  );
};
export default BacktestBadge;
