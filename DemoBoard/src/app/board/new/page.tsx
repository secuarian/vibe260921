import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { createPostAction } from "../actions";
import { PostForm } from "../post-form";

export default function NewPostPage() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-10">
      <Link
        href="/board"
        className={buttonVariants({ variant: "ghost", className: "w-fit -ml-3" })}
      >
        ← 목록으로
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>글쓰기</CardTitle>
        </CardHeader>
        <CardContent>
          <PostForm action={createPostAction} submitLabel="등록" />
        </CardContent>
      </Card>
    </div>
  );
}
