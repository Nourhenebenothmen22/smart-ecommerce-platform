import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewService } from '../../services/reviewService';

export function useReviews() {
  return useQuery({
    queryKey: ['reviews', 'all'],
    queryFn: () => reviewService.getAll(),
  });
}

export function useProductReviews(productId: string) {
  return useQuery({
    queryKey: ['reviews', productId],
    queryFn: () => reviewService.getByProduct(productId),
    enabled: !!productId,
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => reviewService.create(data),
    onSuccess: (_, variables) => {
      const pid = String(variables.product_id ?? variables.productId ?? '');
      if (pid) {
        queryClient.invalidateQueries({ queryKey: ['reviews', pid] });
        queryClient.invalidateQueries({ queryKey: ['product', pid] });
      }
    },
  });
}

export function useUpdateReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      reviewService.update(id, data),
    onSuccess: (_, { data }) => {
      const pid = String(data.product_id ?? data.productId ?? '');
      if (pid) {
        queryClient.invalidateQueries({ queryKey: ['reviews', pid] });
        queryClient.invalidateQueries({ queryKey: ['product', pid] });
      }
    },
  });
}

export function useDeleteReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, productId }: { id: string; productId?: string }) =>
      reviewService.delete(id),
    onSuccess: (_, { productId }) => {
      if (productId) {
        queryClient.invalidateQueries({ queryKey: ['reviews', productId] });
        queryClient.invalidateQueries({ queryKey: ['product', productId] });
      }
    },
  });
}
