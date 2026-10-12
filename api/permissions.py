from rest_framework.permissions import SAFE_METHODS, BasePermission


# Anyone can read a blog; only its author's login account, or staff, can change it
class IsBlogAuthorOrReadOnly(BasePermission):
    message = 'You can only change your own blogs.'

    # Reads pass; writes need the blog's author to be linked to the caller's account
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.is_staff:
            return True
        account_id = obj.user.account_id
        return account_id is not None and account_id == request.user.id
