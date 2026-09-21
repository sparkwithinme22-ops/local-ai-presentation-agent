from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class SlideType(str, Enum):
    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    SECTION = "section"
    QUOTE = "quote"
    CHART = "chart"
    CLOSING = "closing"


class ChartType(str, Enum):
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"


class ChartSeries(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    values: List[float] = Field(min_length=1, max_length=12)


class ChartSpec(BaseModel):
    type: ChartType
    categories: List[str] = Field(min_length=2, max_length=12)
    series: List[ChartSeries] = Field(min_length=1, max_length=4)
    value_axis_title: Optional[str] = Field(default=None, max_length=60)
    source_note: Optional[str] = Field(default=None, max_length=180)

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ChartSpec":
        category_count = len(self.categories)
        if any(len(series.values) != category_count for series in self.series):
            raise ValueError("each chart series must have one value per category")
        if self.type in {ChartType.PIE, ChartType.DOUGHNUT} and len(self.series) != 1:
            raise ValueError("pie and doughnut charts require exactly one series")
        return self


class SlideSpec(BaseModel):
    type: SlideType
    title: str = Field(min_length=1, max_length=90)
    subtitle: Optional[str] = Field(default=None, max_length=160)
    bullets: List[str] = Field(default_factory=list, max_length=6)
    quote: Optional[str] = Field(default=None, max_length=420)
    attribution: Optional[str] = Field(default=None, max_length=160)
    chart: Optional[ChartSpec] = None

    @model_validator(mode="after")
    def validate_slide_content(self) -> "SlideSpec":
        if self.type in {SlideType.CONTENT, SlideType.AGENDA} and not self.bullets:
            raise ValueError(f"{self.type.value} slides require at least one bullet")
        if self.type == SlideType.QUOTE and not self.quote:
            raise ValueError("quote slides require quote text")
        if self.type == SlideType.CHART and not self.chart:
            raise ValueError("chart slides require chart data")
        if self.type == SlideType.CLOSING and (self.bullets or self.chart or self.quote):
            raise ValueError("closing slides may contain only a title and optional subtitle")
        if any(len(item) > 180 for item in self.bullets):
            raise ValueError("bullet text must not exceed 180 characters")
        return self


class PresentationSpec(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    subtitle: Optional[str] = Field(default=None, max_length=180)
    audience: str = Field(min_length=1, max_length=120)
    slides: List[SlideSpec] = Field(min_length=2, max_length=30)

    @model_validator(mode="after")
    def validate_structure(self) -> "PresentationSpec":
        if self.slides[0].type != SlideType.TITLE:
            raise ValueError("the first slide must use type 'title'")
        if self.slides[-1].type != SlideType.CLOSING:
            raise ValueError("the last slide must use type 'closing'")
        return self
