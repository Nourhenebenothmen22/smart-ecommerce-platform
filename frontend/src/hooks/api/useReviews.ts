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
      if (variables.productId) {
        queryClient.invalidateQueries({ queryKey: ['reviews', variables.productId] });
        queryClient.invalidateQueries({ queryKey: ['product', variables.productId] });
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
      if (data.productId) {
        queryClient.invalidateQueries({ queryKey: ['reviews', data.productId] });
        queryClient.invalidateQueries({ queryKey: ['product', data.productId] });
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
