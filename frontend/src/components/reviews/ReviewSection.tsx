import React, { useState } from 'react';
import { MessageSquareText, ShieldCheck, ShoppingBag, Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import {
  useProductReviews,
  useCreateReview,
  useUpdateReview,
  useDeleteReview,
} from '../../hooks/api/useReviews';

function getErrorMessage(error: unknown, fallback: string) {
  if (error && typeof error === 'object' && 'message' in error) {
    return (error as { message: string }).message;
  }
  return fallback;
}

interface Review {
  id: string;
  product_id: number;
  user_id?: string;
  customer_id?: string;
  rating: number;
  review_text?: string;
  comment?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  created_at?: string;
}

interface ReviewSectionProps {
  productId: string;
}

function StarInput({ value, onChange, disabled }: { value: number; onChange: (v: number) => void; disabled?: boolean }) {
  const { t } = useTranslation();
  const [hover, setHover] = useState(0);

  return (
    <div className="review-stars review-stars-input">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => !disabled && onChange(star)}
          onMouseEnter={() => !disabled && setHover(star)}
          onMouseLeave={() => setHover(0)}
          disabled={disabled}
          aria-label={t('reviews.starLabel', { count: star })}
          className={star <= (hover || value) ? 'is-active' : ''}
        >
          {star <= (hover || value) ? '\u2605' : '\u2606'}
        </button>
      ))}
    </div>
  );
}

function StarDisplay({ value }: { value: number }) {
  return (
    <div className="review-stars" aria-hidden="true">
      {[1, 2, 3, 4, 5].map((star) => (
        <span key={star} className={star <= value ? 'is-active' : ''}>
          {star <= value ? '\u2605' : '\u2606'}
        </span>
      ))}
    </div>
  );
}

const ReviewSection: React.FC<ReviewSectionProps> = ({ productId }) => {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const { data: reviews = [] } = useProductReviews(productId);
  const { mutate: createReview, isPending: isCreating } = useCreateReview();
  const { mutate: updateReview, isPending: isUpdating } = useUpdateReview();
  const { mutate: deleteReview, isPending: isDeleting } = useDeleteReview();

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [editId, setEditId] = useState<string | null>(null);
  const [editRating, setEditRating] = useState(0);
  const [editComment, setEditComment] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const isCustomer = user?.role === 'customer';
  const productReviews = Array.isArray(reviews) ? reviews : [];
  const myReview = productReviews.find(
    (review: Review) => review.user_id === user?.id || review.customer_id === user?.id
  );

  const showSuccess = (text: string) => setMessage({ type: 'success', text });
  const showError = (text: string) => setMessage({ type: 'error', text });
  const clearMessage = () => setMessage(null);

  const resetForm = () => {
    setRating(0);
    setComment('');
    setEditId(null);
    setEditRating(0);
    setEditComment('');
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating < 1) return;
    clearMessage();
    createReview(
      { product_id: Number(productId), productId, rating, review_text: comment.trim() },
      {
        onSuccess: () => {
          showSuccess(t('reviews.created'));
          resetForm();
        },
        onError: (err: unknown) => {
          showError(getErrorMessage(err, t('reviews.createError')));
        },
      }
    );
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId || editRating < 1) return;
    clearMessage();
    updateReview(
      { id: editId, data: { productId, rating: editRating, review_text: editComment.trim() } },
      {
        onSuccess: () => {
          showSuccess(t('reviews.updated'));
          resetForm();
        },
        onError: (err: unknown) => {
          showError(getErrorMessage(err, t('reviews.updateError')));
        },
      }
    );
  };

  const handleDelete = (id: string) => {
    if (!window.confirm(t('reviews.deleteConfirm'))) return;
    clearMessage();
    deleteReview(
      { id, productId },
      {
        onSuccess: () => {
          showSuccess(t('reviews.deleted'));
        },
        onError: (err: unknown) => {
          showError(getErrorMessage(err, t('reviews.deleteError')));
        },
      }
    );
  };

  const startEdit = (review: Review) => {
    setEditId(review.id);
    setEditRating(review.rating);
    setEditComment(review.review_text ?? review.comment ?? '');
    setRating(0);
    setComment('');
    clearMessage();
  };

  const cancelEdit = () => {
    resetForm();
    clearMessage();
  };

  const isPending = isCreating || isUpdating || isDeleting;
  const accessMessage = !isAuthenticated
    ? t('reviews.access.loginCustomerOrder')
    : !isCustomer
      ? t('reviews.access.customersOnlyOrder')
      : t('reviews.access.customerReady');

  const accessTone = isAuthenticated && isCustomer ? 'success' : 'warning';

  return (
    <section className="review-panel" aria-labelledby="review-panel-title">
      <div className="review-panel-header">
        <div>
          <span className="review-eyebrow">{t('reviews.eyebrow')}</span>
          <h2 id="review-panel-title">{t('reviews.title')}</h2>
          <p>{t('reviews.subtitle')}</p>
        </div>
        <div className="review-summary">
          <Star size={18} />
          <span>{t('reviews.summary', { count: productReviews.length })}</span>
        </div>
      </div>

      <div className={`review-access-card ${accessTone}`}>
        <div className="review-access-icon">
          {isAuthenticated && isCustomer ? <ShieldCheck size={22} /> : <ShoppingBag size={22} />}
        </div>
        <div>
          <strong>{t('reviews.access.title')}</strong>
          <p>{accessMessage}</p>
        </div>
      </div>

      {message && (
        <div className={`review-message ${message.type}`} role="status">
          {message.text}
        </div>
      )}

      {isAuthenticated && isCustomer && (
        <div className="review-workspace">
          <div className="review-form-card">
            <div className="review-card-heading">
              <MessageSquareText size={20} />
              <div>
                <h3>{editId ? t('reviews.editReview') : myReview ? t('reviews.yourReview') : t('reviews.writeReview')}</h3>
                <p>{editId ? t('reviews.editHint') : myReview ? t('reviews.myReviewHint') : t('reviews.writeHint')}</p>
              </div>
            </div>

            {myReview && !editId && (
              <div className="review-current">
                <div className="review-current-top">
                  <StarDisplay value={myReview.rating} />
                  <div className="review-actions">
                    <button className="btn btn-sm btn-outline" onClick={() => startEdit(myReview)} disabled={isPending}>
                      {t('common.edit')}
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(myReview.id)} disabled={isPending}>
                      {isDeleting ? t('common.loading') : t('common.delete')}
                    </button>
                  </div>
                </div>
                {(myReview.review_text || myReview.comment) && (
                  <p>{myReview.review_text ?? myReview.comment}</p>
                )}
              </div>
            )}

            {editId ? (
              <form onSubmit={handleUpdate} className="review-form">
                <label>
                  <span>{t('reviews.rating')}</span>
                  <StarInput value={editRating} onChange={setEditRating} disabled={isPending} />
                </label>
                <label>
                  <span>{t('reviews.comment')}</span>
                  <textarea
                    id="edit-comment"
                    className="textarea"
                    value={editComment}
                    onChange={(e) => setEditComment(e.target.value)}
                    rows={4}
                    placeholder={t('reviews.commentPlaceholder')}
                  />
                </label>
                <div className="review-form-actions">
                  <button type="submit" className="btn btn-primary" disabled={editRating < 1 || isPending}>
                    {isUpdating ? t('common.saving') : t('common.save')}
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={cancelEdit} disabled={isPending}>
                    {t('common.cancel')}
                  </button>
                </div>
              </form>
            ) : !myReview ? (
              <form onSubmit={handleCreate} className="review-form">
                <label>
                  <span>{t('reviews.rating')}</span>
                  <StarInput value={rating} onChange={setRating} disabled={isPending} />
                </label>
                <label>
                  <span>{t('reviews.comment')}</span>
                  <textarea
                    id="create-comment"
                    className="textarea"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={4}
                    placeholder={t('reviews.commentPlaceholder')}
                  />
                </label>
                <button type="submit" className="btn btn-primary" disabled={rating < 1 || isPending}>
                  {isCreating ? t('common.submitting') : t('reviews.submit')}
                </button>
              </form>
            ) : null}
          </div>
        </div>
      )}
    </section>
  );
};

export default ReviewSection;
