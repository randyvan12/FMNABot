import asyncio
import discord
import logging
import requests
import json
from discord.ext import commands
import numpy as np

#logs info
logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix='$fmna ')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

#doesnt work because the unseen query gets seen shows   
@bot.command()
async def recommend(ctx, anilist_name: str):
    message = await ctx.send("Finding shows to recommend")
    url = "https://graphql.anilist.co"

    #get tags
    tag_query = '''
    query{
        MediaTagCollection{
            name
        }
    }
    '''
    tag_response = requests.post(url, json={'query': tag_query}).json()

    tag_list = []
    for dic in tag_response['data']['MediaTagCollection']:
        tag_list.append(dic['name'])

    tag_map = {k: v for v, k in enumerate(tag_list)}

    user_query = '''
    query($userName: String){
        MediaListCollection(userName: $userName, type: ANIME, status_in: [COMPLETED]){
            lists{
                entries{
                    score
                    media{
                        title{
                            romaji
                        }
                        tags{
                            name
                            rank
                        }
                    }
                }
            }
        }
    }
    '''

    unseen_query = '''
    query($page: Int){
        Page(perPage: 50 page: $page){
                pageInfo{
                    lastPage
                }
            media(onList: false, type: ANIME, isAdult: false, format_in: [TV, MOVIE, ONA], status_in: [FINISHED, RELEASING], 
            startDate_greater: 19800101, popularity_greater: 10000, averageScore_greater: 60){
                siteUrl
                title{
                    romaji
                }
                tags{
                    name
                    rank
                }
            }
        }
    }
    '''

    user_variables = {
        'userName': anilist_name
    }

    user_response = requests.post(url, json={'query': user_query, 'variables': user_variables}).json()
    anime_list = user_response['data']['MediaListCollection']['lists'][0]['entries']

    weights = [0] * len(tag_list)
    for anime in anime_list:
        for tag in anime['media']['tags']:
            weights[tag_map[tag['name']]] += anime['score'] * tag['rank']


    
    unseen_list = []
    for i in range(1, 30):
        unseen_variables = {
            'page': i,
        }
        unseen_response = requests.post(url, json = {'query': unseen_query, 'variables': unseen_variables}).json()
        for unseen_anime in unseen_response['data']['Page']['media']:
            num_of_anime = 0
            for seen_anime in anime_list:
                num_of_anime+=1
                if unseen_anime['title']['romaji'] == seen_anime['media']['title']['romaji']:
                    break
                elif num_of_anime == len(anime_list):
                    unseen_list.append(unseen_anime)
                    break
         
    scores = []
    for anime in unseen_list:
        score = 0
        for tag in anime['tags']:
            score += weights[tag_map[tag['name']]] * tag['rank']
        scores.append(score * -1)

    rankings = np.argsort(scores)
    rankings = rankings[:50]
    recommendation_list = []

    for index in rankings:
        anime_info = {}
        # anime_info['id'] = unseen_list[index]['id']
        # anime_info['img_URL'] = unseen_list[index]['coverImage']['medium']
        # anime_info['romaji'] = unseen_list[index]['title']['romaji']
        anime_info['site_URL'] = unseen_list[index]['siteUrl']
        recommendation_list.append(anime_info)
    pages = len(recommendation_list)
    cur_page = 1
    # print(recommendation_list)
    await message.edit(content=f"Page {cur_page}/{pages}:\n{recommendation_list[cur_page-1]['site_URL']}")
    # getting the message object for editing and reacting

    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
        # This makes sure nobody except the command sender can interact with the "menu"
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            # waiting for a reaction to be added - times out after x seconds, 60 in this
            # example

            if str(reaction.emoji) == "▶️" and cur_page != pages:
                cur_page += 1
                await message.edit(content=f"Page {cur_page}/{pages}:\n{recommendation_list[cur_page-1]['site_URL']}")
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                cur_page -= 1
                await message.edit(content=f"Page {cur_page}/{pages}:\n{recommendation_list[cur_page-1]['site_URL']}")
                await message.remove_reaction(reaction, user)

            else:
                await message.remove_reaction(reaction, user)
                # removes reactions if the user tries to go forward on the last page or
                # backwards on the first page
        except asyncio.TimeoutError:
            await message.delete()
            break
            # ending the loop if user doesn't react after x seconds

bot.run('NzY5NzUzODAzMDE5OTExMTkw.X5TnFw.VUEjFmIZ43RSWxZU_ASQ6H3kdx8')
