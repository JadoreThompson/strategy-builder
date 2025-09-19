import { useEffect, useRef } from "react";

const useIntersectionObserver = <T extends HTMLElement>(onIntersecting: () => void) => {
  const refObj = useRef<T | null>(null);

  useEffect(() => {
    if (!refObj.current) return;

    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          onIntersecting();
        }
      });
    });

    obs.observe(refObj.current);

    return () => {
      if (refObj.current) {
        obs.unobserve(refObj.current);
      }

      obs.disconnect();
    };
  }, [refObj]);

  return { refObj };
};

export default useIntersectionObserver;
