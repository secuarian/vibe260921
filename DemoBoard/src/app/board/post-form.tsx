"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import type { FormState } from "./actions";

type PostFormProps = {
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
  defaultValues?: {
    title: string;
    author: string;
    content: string;
  };
};

const initialState: FormState = {};

export function PostForm({ action, submitLabel, defaultValues }: PostFormProps) {
  const [state, formAction, isPending] = useActionState(action, initialState);

  return (
    <form action={formAction} className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <Label htmlFor="title">제목</Label>
        <Input
          id="title"
          name="title"
          placeholder="제목을 입력하세요"
          defaultValue={defaultValues?.title}
          maxLength={100}
          required
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="author">작성자</Label>
        <Input
          id="author"
          name="author"
          placeholder="이름을 입력하세요"
          defaultValue={defaultValues?.author}
          maxLength={30}
          required
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="content">내용</Label>
        <Textarea
          id="content"
          name="content"
          placeholder="내용을 입력하세요"
          defaultValue={defaultValues?.content}
          rows={10}
          required
        />
      </div>

      {state.error && (
        <p className="text-sm font-medium text-destructive">{state.error}</p>
      )}

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? "저장 중..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
