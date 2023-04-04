import csv

import torch  # Deep learning - NOT USED
import numpy as np  # Data analysis
import pandas as pd  # Data analysis
import matplotlib.pyplot as plt  # Plot data
from sklearn.feature_extraction.text import TfidfVectorizer  # Machine learning
from sklearn.metrics.pairwise import cosine_similarity  # Machine learning
import time


class DataProcessor:
    def __init__(self):
        # =======================
        # Data Processing
        # =======================
        self.image_links = None
        print("Reading files")
        self.movies = pd.read_csv("movies-short.csv")  # Parsing movies
        self.ratings = pd.read_csv("ratings-short.csv")  # Parsing ratings
        self.genome_tags = pd.read_csv('genome-tags.csv')  # Parsing genome tags
        self.genome_scores = pd.read_csv('genome-scores.csv')  # Parsing genome relevance
        self.movie_posters = pd.read_csv('image.csv')   # Parsing movie posters

        # Merging genome tags and their relevance
        genome_merge = pd.merge(self.genome_tags, self.genome_scores, on='tagId')[
            ['movieId', 'tagId', 'tag', 'relevance']]

        # Taking only tags with relevance higher than 0.3
        all_tags = genome_merge[genome_merge.relevance > 0.3][['movieId', 'tagId', 'tag']]

        all_tags['tagId'] = all_tags.tagId.astype(str)

        def _merge_all_tags(tags):
            combined = ' '.join(set(tags))
            return combined

        # Merging all genome tags to the related movies
        self.movies_tags = all_tags.groupby('movieId')['tagId'].agg(_merge_all_tags)  # Merge all tags
        self.movies_tags.name = 'moviesTags'  # Rename the new column as 'movieTags'
        self.movies_tags = self.movies_tags.reset_index()  # Add the new column

        # Aggregating mean, median and size functions over the grouped data
        avg_rating = self.ratings.groupby('movieId')['rating'].agg(['mean', 'median', 'size'])
        avg_rating.columns = ['mean', 'median', 'numRatings']  # Name the new columns
        avg_rating = avg_rating.reset_index()  # Add the new columns

        # Taking only movies with 300+ number of ratings
        min_num_ratings = avg_rating['numRatings'].quantile(
            0.8)  # Only work on movies with more ratings than 80% others
        self.popular_movies = avg_rating[avg_rating.numRatings > min_num_ratings][
            ['movieId', 'mean', 'median', 'numRatings']]

        # Weighted ratings calculation formula from IMDB
        C = self.popular_movies['mean'].mean()  # ~ 3.29 rating

        def _weighted_rating(movie, min_num_ratings=min_num_ratings, C=C):
            V = movie['numRatings']
            R = movie['mean']
            return (V / (V + min_num_ratings) * R) + (min_num_ratings / (min_num_ratings + V) * C)

        # Apply the weighted ratings
        self.popular_movies['weightedRatings'] = self.popular_movies.apply(_weighted_rating, axis=1)
        # self.popular_movies = self.popular_movies.sort_values('weightedRatings', ascending=False)         # Sort
        self.popular_movies = self.popular_movies.sort_values('numRatings', ascending=False)

        # Merge to get all tags
        self.popular_movies = pd.merge(self.popular_movies, self.movies, how='left', on='movieId')
        ratings_and_tags_full = pd.merge(self.popular_movies, self.movies_tags, how='left', on='movieId')

        # Removing the null data
        self.ratings_and_tags = ratings_and_tags_full[~ratings_and_tags_full.moviesTags.isnull()].reset_index(drop=True)

        # Graphing
        """
        graph = pd.merge(self.popular_movies, movies, on='movieId')[['movieId', 'title', 'numRatings', 'weightedRatings']]
        plt.barh(graph['title'].head(10), graph['numRatings'].head(10), align='center', color='red')
        plt.gca().invert_yaxis()
        plt.xlabel('numRatings')
        plt.ylabel('titles')
        plt.show()
        """

        # =======================
        # Machine Learning
        # =======================

        # Using Term Frequency - Inverse Document Frequency (TF-IDF) to transform movies genome tags
        # into number representations
        # https://medium.com/@cmukesh8688/tf-idf-vectorizer-scikit-learn-dbc0244a911a
        tfidf_vect = TfidfVectorizer()  # Instantiating the vectorizer object
        self.vectorized_tags = tfidf_vect.fit_transform(
            self.ratings_and_tags.moviesTags)  # Transform the tags into numbers

        # Using cosine similarity to compare the relationship between tags and movies
        # https://www.sciencedirect.com/topics/computer-science/cosine-similarity
        # Transform into data frame for processing
        # self.data = pd.DataFrame(cosine_similarity(self.vectorized_tags))

        # Creating a vectorized matrix
        self.ratings_and_tags = self.ratings_and_tags.sort_values('movieId',
                                                                  ascending=True)  # Sort according to movieId
        # movies_indexing = self.ratings_and_tags['movieId']

        # mxm matrix with both row and columns representing movieId
        # diagonal will be 1, matrix[m][n] represents how relevant movie m is to movie n according to tags/ genres
        # self.data.columns = [str(movies_indexing[int(col)]) for col in self.data.columns]
        # self.data.index = [movies_indexing[index] for index in self.data.index]

        print("Done")

    def recommend_popularity(self):
        print("=======================")
        print("Top 10 suggestions: ")
        print(self.popular_movies['title'].head(10))
        print("=======================")

    def recommend_userId(self, userId):
        # If there is only 1 user and that user doesn't have any rating history yet, recommend most popular movies by
        # rating. This avoids cold start
        if len(userId) == 1 and (int(userId[0]) not in self.ratings['userId'].values):
            return self.popular_movies['movieId'].values.tolist()[0:20]

        # If the first user does not have any ratings yet, get from the most popular movies to avoid crashing
        if int(userId[0]) not in self.ratings['userId'].values:
            user_ratings = self.ratings.sample(10)

        # Else combine all the other user data to make recommendation
        else:
            user_ratings = self.ratings[self.ratings.userId == int(userId[0])]

        def _balance_ratings(ur):
            rating = ur['rating']
            id_num = ur['userId']
            num_ratings = self.ratings[self.ratings.userId == int(id_num)].size
            return rating / num_ratings

        # num_ratings = self.ratings[self.ratings.userId == int(userId[0])]['rating'].size
        # user_ratings['weight'] = user_ratings.loc[:, 'rating']
        # user_ratings['weight'] = user_ratings.apply(_balance_ratings, axis=1)
        for i in range(1, len(userId)):
            # Getting weighted ratings so that users with more ratings don't dominate the suggestions
            # next_num_ratings = self.ratings[self.ratings.userId == int(userId[0])]['rating'].size
            # print(next_num_ratings)
            if int(userId[i]) not in self.ratings['userId'].values:
                next_user_ratings = self.ratings.sample(10)
            else:
                next_user_ratings = self.ratings[self.ratings.userId == int(userId[i])]
            # next_user_ratings['weight'] = next_user_ratings.apply(_balance_ratings, axis=1)
            # next_user_ratings['weight'] = next_user_ratings.loc[:, 'rating']

            # print(next_user_ratings[['userId', 'rating']])
            # next_user_ratings['weight'] = next_user_ratings.loc[:, 'rating'] / next_user_ratings
            # Combining
            user_ratings = pd.concat([user_ratings, next_user_ratings], ignore_index=True)

        # Recommendations
        user_data = self.ratings_and_tags.reset_index().merge(user_ratings, on='movieId')  # Set of user data
        user_data['weight'] = user_data['rating']/5
        user_profile = np.dot(self.vectorized_tags[user_data['index'].values].toarray().T, user_data['weight'].values)
        cos_sim = cosine_similarity(np.atleast_2d(user_profile), self.vectorized_tags)  # Vectorized the ratings
        R = np.argsort(cos_sim)[:, ::-1]  # Sort the ratings
        recommendations = [i for i in R[0] if i not in user_data['index'].values]  # Get top movies that are not rated
        return self.ratings_and_tags['movieId'][recommendations].head(20).tolist()

        


class UI(DataProcessor):
    def __init__(self):
        self.dp = DataProcessor()
        self.val = 0
        self.curUsernames = []
        self.curUserIds = []
        self.users = {}
        self.update_users()

    def update_users(self):
        file = open("users.txt")
        while True:
            line = file.read()
            if not line:
                break
            split = line.split("\n")
            for x in split:
                txt = x.split()
                if len(txt) == 2:
                    self.users[txt[0]] = txt[1]
        print(self.users)
        file.close()

    def update_ratings(self):
        self.dp = DataProcessor()  # Re-initialize

    def create_user(self):
        username = input("Please enter new username: ")
        file = open("users.txt", "a")
        to_write = username + " "
        if len(self.users) == 0:
            to_write += str(self.dp.ratings['userId'].max() + 1)
        else:
            if username in self.users.keys():
                print("Username already exists. Please try again")
            else:
                cur_id = int(max(self.users.values())) + 1
                to_write += str(cur_id)
        to_write += "\n"
        file.write(to_write)
        file.close()
        self.update_users()

    def add_rating(self):
        if len(self.curUsernames) < 1:
            print("No user logged in yet. Please log in first")
            return

        available = ""
        for s in self.curUsernames:
            available += s + " "
        print("Currently logged in users: " + available)
        username = str(input("Select an user to add rating for: "))
        to_add = []

        # Ask for ratings
        if username in self.curUsernames:
            print("Follow the inquiries, or type DONE!! to quit")
            while True:
                movie_name = str(input("Movie name: "))
                if movie_name == "DONE!!":
                    break
                elif movie_name not in self.dp.movies['title'].values:
                    print("Invalid movie name" + "\n ----")
                else:
                    movie_id = self.dp.movies['movieId'][self.dp.movies.title == movie_name].values.tolist()[0]
                    rating = float(input("Rating from 0.5 to 5: "))
                    cur_time = int(time.time())
                    rating_info = [self.users.get(username), movie_id, rating, cur_time]
                    to_add.append(rating_info)
                    print(to_add)
            # Add the ratings
            file = open('ratings-short.csv', "a")
            for info in to_add:
                writer = csv.writer(file)
                writer.writerow(info)
            file.close()
            #self.update_ratings()

        else:
            print("Invalid username entered")

    def get_recommendation(self):
        available = ""
        for s in self.curUsernames:
            available += s + " "
        print("Currently logged in users: " + available)
        user_to_recommend = []
        username = input("Enter userId for recommendation or ALL for group recommendation: ")
        username = str(username)
        if username in self.curUsernames:
            user_to_recommend.append(self.users.get(username))
            self.dp.recommend_userId(user_to_recommend)
        elif username == "ALL":
            self.dp.recommend_userId(self.curUserIds)
        else:
            print("Invalid username entered")

    def login(self):
        username = ""
        available = ""
        for s in self.users.keys():
            available += s + " "
        print("Currently available users: " + available)
        while username not in self.users.keys():
            username = str(input("Enter a valid username or quit to dismiss: "))
            if username == "quit":
                print("Dismissing")
                return
        self.curUserIds.append(self.users.get(username))
        self.curUsernames.append(username)
        print("Successfully logged into account: " + username)

    def interact(self):
        while self.val < 9:
            print("Please choose from the following interactions")
            print("1: Create new user")
            print("2: Add movie ratings")
            print("3: Get recommendations")
            print("8: Log in to existing accounts")
            print("9: Quit")
            self.val = input("Your command: ")
            self.val = int(self.val)

            if self.val == 1:
                self.create_user()
            if self.val == 2:
                self.add_rating()
            if self.val == 3:
                if len(self.users) == 0:
                    print("No users available. Please create users first")
                elif len(self.curUsernames) == 0:
                    print("No users logged in yet. Please log in first")
                else:
                    self.get_recommendation()
            if self.val == 8:
                self.login()


def main():
    ui = UI()
    ui.interact()


if __name__ == "__main__":
    main()
