# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 18:14:10 2015

"""   

import math

#################################################
# recommender class does item-based filtering and recommends items 
class ItemBasedFilteringRecommender:
    # class variables:    
    # none
    
    ##################################
    # class instantiation method - initializes instance variables
    #
    # usersItemRatings:
    # users item ratings data is in the form of a nested dictionary:
    # at the top level, we have User Names as keys, and their Item Ratings as values;
    # and Item Ratings are themselves dictionaries with Item Names as keys, and Ratings as values
    # Example: 
    #     {"Angelica":{"Blues Traveler": 3.5, "Broken Bells": 2.0, "Norah Jones": 4.5, "Phoenix": 5.0, "Slightly Stoopid": 1.5, "The Strokes": 2.5, "Vampire Weekend": 2.0},
    #      "Bill":{"Blues Traveler": 2.0, "Broken Bells": 3.5, "Deadmau5": 4.0, "Phoenix": 2.0, "Slightly Stoopid": 3.5, "Vampire Weekend": 3.0}}
    #
    # metric:
    # metric is in the form of a string. it can be any of the following:
    # "slopeone", "cosine"
    # defaults to "slopeone"
    #
    # m:
    # the maximum number of recommendations to provide
    # defaults to 50
    #
    # minR and maxR:
    # min and max values of ratings scale
    # defauls to 1 and 5 respectively
    #
    def __init__(self, usersItemRatings, metric='slopeone', m=50, minR=1, maxR=5):
        
        # set usersItemRatings
        self.usersItemRatings = usersItemRatings
        
        # create transpose of itemsUserRatings
        self.itemsUserRatings = {}
        for user in self.usersItemRatings:
            for item in self.usersItemRatings[user]:
                if item not in self.itemsUserRatings:
                    self.itemsUserRatings[item] = {}
                self.itemsUserRatings[item][user] = self.usersItemRatings[user][item]  
                
        # set items list
        self.items = sorted(self.itemsUserRatings.keys())  
        
        # set self.metric and self.similarityFn, and call corresponding initialization methods 
        if metric.lower() == 'cosine':           
            self.metric = metric            
            self.similarityFn = self.adjustedConsineFn
            self.adjustedConsineInitFn()
        elif metric.lower() == 'slopeone':
            self.metric = 'slopeone'            
            self.similarityFn = self.weightedSlopeOneFn
            self.weightedSlopeOneInitFn()
        else:
            print ("    (DEBUG - metric not in (cosine, slopeone) - defaulting to slopeone)")
            self.metric = 'slopeone'
            self.similarityFn = self.weightedSlopeOneFn
            self.weightedSlopeOneInitFn()
        
        # set m
        if m > 0:   
            self.m = m
        else:
            print ("    (DEBUG - invalid value of m (must be > 0) - defaulting to 50)")
            self.m = 50      
        
        # set minR and maxR 
        self.minR = minR
        self.maxR = maxR
 
    ##################################
    # Adjusted Cosine Item Based Filtering - Initialization
    def adjustedConsineInitFn(self):
        
        # get average ratings per user
        self.userAvgRatings = {}
        for (user, ratings) in self.usersItemRatings.items():
            self.userAvgRatings[user] = round((float(sum(ratings.values()))/len(ratings.values())), 2)
        #print (self.userAvgRatings)
        
        # create similarity matrix
        self.similarityMatrix = {}
        for itemX in self.items:
            for itemY in self.items:
                if itemX == itemY:
                    continue
                num, den1, den2 = 0, 0, 0 
                for (user, ratings) in self.usersItemRatings.items():
                    if itemX in ratings and itemY in ratings:
                        avg = self.userAvgRatings[user]
                        num += (ratings[itemX] - avg) * (ratings[itemY] - avg)
                        den1 += (ratings[itemX] - avg)**2
                        den2 += (ratings[itemY] - avg)**2
                if den1!=0 and den2!=0:
                    if itemX not in self.similarityMatrix:
                        self.similarityMatrix[itemX] = {}
                    self.similarityMatrix[itemX][itemY] = round (num / (math.sqrt(den1) * math.sqrt(den2)), 2)      
        #print (self.similarityMatrix)
        
    ##################################
    # Adjusted Cosine Item Based Filtering
    def adjustedConsineFn(self, userX):        
        
        # get normalized userX ratings
        self.userXItemRatingsNorm = {}
        for item in self.usersItemRatings[userX]:
            self.userXItemRatingsNorm[item] = (2*(self.usersItemRatings[userX][item]-self.minR)-(self.maxR-self.minR))/(self.maxR-self.minR)
        #print(self.userXItemRatingsNorm)
        
        # get normalized predicted ratings (for items that user hasn't rated yet)
        self.userXItemRatingsNormPred = {}
        for item in self.items:
            if (item not in self.userXItemRatingsNorm):
                self.userXItemRatingsNormPred[item] = 0          
        for itemk in self.userXItemRatingsNormPred:
            num, den = 0, 0
            for itemj in self.userXItemRatingsNorm:
                if itemj in self.similarityMatrix and itemk in self.similarityMatrix[itemj]:
                    num += self.similarityMatrix[itemj][itemk]*self.userXItemRatingsNorm[itemj]
                    den += abs(self.similarityMatrix[itemj][itemk])
            if den!=0:
                self.userXItemRatingsNormPred[itemk] = round(num/den, 3)
        #print (self.userXItemRatingsNormPred)
                
        # get de-normalized predicted ratings (for items that user hasn't rated yet)
        self.userXItemRatingsPred = {}
        for item in self.userXItemRatingsNormPred:
            self.userXItemRatingsPred[item] = round(0.5*((self.userXItemRatingsNormPred[item]+1)*(self.maxR-self.minR))+self.minR, 3)   
        #print (self.userXItemRatingsPred)
        
        userXItemRatingsPredL = list(self.userXItemRatingsPred.items())
        userXItemRatingsPredL.sort(key=lambda tup:tup[1], reverse=True)                  
        userXItemRatingsPredL = [(k,round(v, 2)) for (k, v) in userXItemRatingsPredL]
        return userXItemRatingsPredL[:self.m]
 
    ##################################
    # Weighted Slope One Item Based Filtering - Initialization      
    def weightedSlopeOneInitFn(self):
        
        # compute deviation and frequency matrices
        self.deviationMatrix = {}
        self.frequencyMatrix = {}
        for itemX in self.items:
            for itemY in self.items:
                if itemX == itemY:
                    continue
                num, den = 0, 0
                for (user, ratings) in self.usersItemRatings.items():
                    if itemX in ratings and itemY in ratings:
                        num += (ratings[itemX] - ratings[itemY])
                        den += 1
                if den!=0:
                    if itemX not in self.deviationMatrix:
                        self.deviationMatrix[itemX] = {}
                        self.frequencyMatrix[itemX] = {}
                    self.deviationMatrix[itemX][itemY] = round (num/den, 2)
                    self.frequencyMatrix[itemX][itemY] = den
        #print(self.deviationMatrix)
        #print(self.frequencyMatrix)

    ##################################
    # Weighted Slope One Item Based Filtering       
    def weightedSlopeOneFn(self, userX):

        # get predicted ratings (for items that user hasn't rated yet)
        self.userXItemRatingsPred = {}
        for item in self.items:
            if (item not in self.usersItemRatings[userX]):
                self.userXItemRatingsPred[item] = 0

        for itemk in self.userXItemRatingsPred:
            num, den = 0, 0
            for itemj in self.usersItemRatings[userX]:
                if itemj in self.deviationMatrix and itemk in self.deviationMatrix[itemj]:
                    num += (self.deviationMatrix[itemk][itemj]+self.usersItemRatings[userX][itemj])*self.frequencyMatrix[itemk][itemj]
                    den += self.frequencyMatrix[itemk][itemj]
            if den!=0:
                self.userXItemRatingsPred[itemk] = round(num/den, 3)
                # adjust ratings that exceed scale as per:                
                # http://lemire.me/fr/documents/publications/lemiremaclachlan_sdm05.pdf
                if (self.userXItemRatingsPred[itemk]>self.maxR):
                    self.userXItemRatingsPred[itemk]=self.maxR
        #print(self.userXItemRatingsPred)   
                
        userXItemRatingsPredL = list(self.userXItemRatingsPred.items())
        userXItemRatingsPredL.sort(key=lambda tup:tup[1], reverse=True)                  
        userXItemRatingsPredL = [(k,round(v, 2)) for (k, v) in userXItemRatingsPredL]
        return userXItemRatingsPredL[:self.m]
       
    ##################################
    # Make recommendation for UserX        
    def recommend(self, userX): 
        return self.similarityFn(userX)

