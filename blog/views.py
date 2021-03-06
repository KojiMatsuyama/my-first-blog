from django.shortcuts import render
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from .models import Post
from .forms import PostForm

def post_new(request):
    form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

# Create your views here.

def post_list(request):
#    posts = Post.objects.filter(created_date=timezone.now()).order_by('created_date')
    posts = Post.objects.all()
    return render(request, 'blog/post_list.html', {'posts' : posts})

def post_detail(request,pk):
    post = get_object_ir_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def page(request):
    form = PostForm()
    return render(request, 'blog/page.html', {'form' : form})
