import { ChevronUp } from "lucide-react";
import { useEffect, useState, type FC } from "react";

const ScrollTop: FC = () => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const handleOnScroll = () => setShow(window.scrollY > window.innerHeight);
    document.addEventListener("scroll", handleOnScroll);

    return () => {
      document.removeEventListener("scroll", handleOnScroll);
    };
  }, []);

  return (
    <div
      className={`fixed right-4 bottom-4 flex h-10 w-10 items-center justify-center rounded-full border-1 border-stone-300 shadow-sm transition-all duration-500 ease-in-out ${show ? "translate-y-0" : "translate-y-100"}`}
    >
      <ChevronUp
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className="cursor-pointer text-stone-900"
      />
    </div>
  );
};
export default ScrollTop;
