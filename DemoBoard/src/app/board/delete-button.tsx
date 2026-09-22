"use client";

import { useTransition } from "react";

import { Button } from "@/components/ui/button";

type DeleteButtonProps = {
  action: () => Promise<void>;
};

export function DeleteButton({ action }: DeleteButtonProps) {
  const [isPending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="destructive"
      disabled={isPending}
      onClick={() => {
        if (!confirm("정말 삭제하시겠습니까?")) return;
        startTransition(() => {
          action();
        });
      }}
    >
      {isPending ? "삭제 중..." : "삭제"}
    </Button>
  );
}
