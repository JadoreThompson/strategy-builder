import type { FC } from "react";

const Spinner: FC = () => {
  return (
    <div className="flex h-8 w-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-transparent"></div>
    </div>
  );
};
export default Spinner;
