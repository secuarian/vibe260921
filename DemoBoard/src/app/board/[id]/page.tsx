import Link from "next/link";
import { notFound } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getPost, incrementViews } from "@/lib/posts";

import { deletePostAction } from "../actions";
import { DeleteButton } from "../delete-button";

function formatDate(iso: string) {
  const date = new Date(iso);
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function PostDetailPage(
  props: PageProps<"/board/[id]">,
) {
  const { id } = await props.params;
  const post = await getPost(id);
  if (!post) notFound();

  await incrementViews(id);

  const removePost = async () => {
    "use server";
    await deletePostAction(id);
  };

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
          <CardTitle className="text-xl">{post.title}</CardTitle>
          <div className="flex flex-wrap gap-x-3 text-sm text-muted-foreground">
            <span>{post.author}</span>
            <span>{formatDate(post.createdAt)}</span>
            <span>조회 {post.views}</span>
          </div>
        </CardHeader>
        <Separator />
        <CardContent>
          <p className="whitespace-pre-wrap leading-relaxed">{post.content}</p>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Link
          href={`/board/${post.id}/edit`}
          className={buttonVariants({ variant: "outline" })}
        >
          수정
        </Link>
        <DeleteButton action={removePost} />
      </div>
    </div>
  );
}
