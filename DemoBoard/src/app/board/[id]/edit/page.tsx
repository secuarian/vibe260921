import Link from "next/link";
import { notFound } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getPost } from "@/lib/posts";

import { updatePostAction, type FormState } from "../../actions";
import { PostForm } from "../../post-form";

export default async function EditPostPage(
  props: PageProps<"/board/[id]/edit">,
) {
  const { id } = await props.params;
  const post = await getPost(id);
  if (!post) notFound();

  const action = async (prevState: FormState, formData: FormData) => {
    "use server";
    return updatePostAction(id, prevState, formData);
  };

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-4 py-10">
      <Link
        href={`/board/${id}`}
        className={buttonVariants({ variant: "ghost", className: "w-fit -ml-3" })}
      >
        ← 돌아가기
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>글 수정</CardTitle>
        </CardHeader>
        <CardContent>
          <PostForm
            action={action}
            submitLabel="수정 완료"
            defaultValues={{
              title: post.title,
              author: post.author,
              content: post.content,
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
