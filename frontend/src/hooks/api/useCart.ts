import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartService } from '../../services/cartService';

export function useCart(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['cart'],
    queryFn: () => cartService.getCart(),
    ...options,
  });
}

export function useAddToCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      cartService.addItem(productId, quantity),
    onMutate: async ({ productId, quantity }) => {
      await queryClient.cancelQueries({ queryKey: ['cart'] });
      const previousCart = queryClient.getQueryData(['cart']);
      queryClient.setQueryData(['cart'], (old: any) => {
        if (!old) return [{ product_id: productId, quantity }];
        const isArrayCart = Array.isArray(old);
        const items = isArrayCart ? old : old.items ?? [];
        const nextItems = [...items];
        const existingIndex = nextItems.findIndex((item: any) => String(item.product?.id ?? item.product_id) === String(productId));

        if (existingIndex >= 0) {
          nextItems[existingIndex] = {
            ...nextItems[existingIndex],
            quantity: Number(nextItems[existingIndex].quantity ?? 0) + quantity,
          };
        } else {
          nextItems.unshift({ product_id: productId, quantity });
        }

        return isArrayCart ? nextItems : { ...old, items: nextItems };
      });
      return { previousCart };
    },
    onError: (_error, _variables, context) => {
      if (context && 'previousCart' in context) {
        queryClient.setQueryData(['cart'], context.previousCart);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}

export function useUpdateCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      cartService.updateItem(productId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}

export function useRemoveFromCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (productId: string) => cartService.removeItem(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}
