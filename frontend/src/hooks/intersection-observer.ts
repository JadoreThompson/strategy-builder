import { useEffect, useRef } from "react";

const useIntersectionObserver = <T extends HTMLElement>(onIntersecting: () => void) => {
  const elementRefObj = useRef<T | null>(null);

  useEffect(() => {
    if (!elementRefObj.current) return;

    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          onIntersecting();
        }
      });
    });

    obs.observe(elementRefObj.current);

    return () => {
      if (elementRefObj.current) {
        obs.unobserve(elementRefObj.current);
      }

      obs.disconnect();
    };
  }, [elementRefObj]);

  return { elementRefObj };
};

export default useIntersectionObserver;
