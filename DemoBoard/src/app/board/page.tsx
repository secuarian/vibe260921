import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getPosts } from "@/lib/posts";

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

export default async function BoardPage() {
  const posts = await getPosts();

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">DemoBoard</h1>
          <p className="text-sm text-muted-foreground">
            총 {posts.length}개의 게시글이 있습니다.
          </p>
        </div>
        <Link href="/board/new" className={buttonVariants()}>
          글쓰기
        </Link>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16 text-center">번호</TableHead>
              <TableHead>제목</TableHead>
              <TableHead className="w-32">작성자</TableHead>
              <TableHead className="w-40">작성일</TableHead>
              <TableHead className="w-20 text-center">조회수</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                  등록된 게시글이 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              posts.map((post, index) => (
                <TableRow key={post.id}>
                  <TableCell className="text-center text-muted-foreground">
                    {posts.length - index}
                  </TableCell>
                  <TableCell className="max-w-0 truncate">
                    <Link
                      href={`/board/${post.id}`}
                      className="hover:underline"
                    >
                      {post.title}
                    </Link>
                  </TableCell>
                  <TableCell>{post.author}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(post.createdAt)}
                  </TableCell>
                  <TableCell className="text-center text-muted-foreground">
                    {post.views}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
