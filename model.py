from pydantic import BaseModel, Field
from typing import List

# Define sub-models
class SentimentRow(BaseModel):
    User_Type: str = Field(..., alias="User Type")
    Positive_Sentiment: str = Field(..., alias="Positive Sentiment")
    Negative_Sentiment: str = Field(..., alias="Negative Sentiment")
    Key_Themes: str = Field(..., alias="Key Themes")

class ProsConsItem(BaseModel):
    title: str
    description: str
    example: str

class CopySummary(BaseModel):
    url: str
    alignment_score: int
    summary: str
    strengths: List[str]
    gaps: List[str]

class MessagingSuggestion(BaseModel):
    core_idea_heading : str = Field(..., alias="core_idea_heading",description="i want to generate the core idea heading like that `Showcase Diverse Practice Areas` not that `Core Idea #1` generate")
    suggestion: str
    why_it_works: str
    where_to_add: str

class HeadlineSuggestion(BaseModel):
    headline: str
    subhead: str
    why_it_works: str


class CTASuggestion(BaseModel):
    cta: str = Field(..., alias="cta", description="i want only cta headings.")
    why_it_works: str 



class OverallSentimentAnalysis(BaseModel):
    Sentiment_Breakdown: List[SentimentRow] = Field(..., alias="Sentiment Data")
    Summary: str = Field(..., alias="#Summary", description="Summary of the sentiment analysis 100 words")


class CustomerReviewAnalysis(BaseModel):
    Customer_Review_Analysis: str = Field(..., alias="#Customer Review Analysis", description="Customer Review Analysis must be 100 words")
    What_You_Get: List[str] = Field(..., alias="#What you’ll get from this document")
    Disclaimer: str = Field(..., alias="#Disclaimer", description="Disclaimer must be 100 words")
    Overall_Sentiment_Analysis: OverallSentimentAnalysis = Field(..., alias="#Overall Sentiment Analysis")
    Pros: List[ProsConsItem] = Field(..., alias="#Pros",description="i want at least 7 items of pros")
    Cons: List[ProsConsItem] = Field(..., alias="#Cons", description="i want at least 7 items cons")
    Existing_Copy_Summary: CopySummary = Field(..., alias="#Existing Copy Summary")
    Messaging_Suggestions: List[MessagingSuggestion] = Field(..., alias="#General Copy & Messaging Suggestions")
    Headline_Suggestions: List[HeadlineSuggestion] = Field(..., alias="#Headline & Subhead Suggestions")
    CTA_Suggestions: List[CTASuggestion] = Field(..., alias="#CTA Suggestions")
    CTA_Overall_Why_It_Works: str = Field(..., alias="overall_why_it_works")
    Conclusion: str = Field(..., alias="#Conclusion",description="Conclusion must be 100 words")
    