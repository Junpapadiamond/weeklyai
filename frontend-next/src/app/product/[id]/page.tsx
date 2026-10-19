import { notFound } from "next/navigation";
import { ProductDetail } from "@/components/product/product-detail";
import { getProductById, getRelatedProducts } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [product, related] = await Promise.all([getProductById(id), getRelatedProducts(id, 6)]);
  if (!product) notFound();
  return <ProductDetail key={id} product={product} related={related} />;
}
