from django.contrib import admin
from .models import TaggedSong,FullLyrics

@admin.register(TaggedSong)
class TaggedSongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'tags')
    search_fields = ('title', 'artist')

# @admin.register(FavoriteSong)
# class FavoriteSongAdmin(admin.ModelAdmin):
#     list_display = ('title', 'artist', 'user', 'created_at')
#     search_fields = ('title', 'artist', 'user__username')

#     list_filter = ['user'] 

@admin.register(FullLyrics)
class FullLyricsAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'created_at')