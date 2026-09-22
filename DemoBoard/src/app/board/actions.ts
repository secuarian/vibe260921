"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import * as posts from "@/lib/posts";

export type FormState = {
  error?: string;
};

function readFields(formData: FormData) {
  const title = String(formData.get("title") ?? "").trim();
  const author = String(formData.get("author") ?? "").trim();
  const content = String(formData.get("content") ?? "").trim();
  return { title, author, content };
}

function validate(fields: { title: string; author: string; content: string }) {
  if (!fields.title) return "제목을 입력해주세요.";
  if (!fields.author) return "작성자를 입력해주세요.";
  if (!fields.content) return "내용을 입력해주세요.";
  if (fields.title.length > 100) return "제목은 100자 이내로 입력해주세요.";
  return null;
}

export async function createPostAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const fields = readFields(formData);
  const error = validate(fields);
  if (error) return { error };

  const post = await posts.createPost(fields);
  revalidatePath("/board");
  redirect(`/board/${post.id}`);
}

export async function updatePostAction(
  id: string,
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const existing = await posts.getPost(id);
  if (!existing) return { error: "게시글을 찾을 수 없습니다." };

  const fields = readFields(formData);
  const error = validate(fields);
  if (error) return { error };

  await posts.updatePost(id, fields);
  revalidatePath("/board");
  revalidatePath(`/board/${id}`);
  redirect(`/board/${id}`);
}

export async function deletePostAction(id: string): Promise<void> {
  await posts.deletePost(id);
  revalidatePath("/board");
  redirect("/board");
}
