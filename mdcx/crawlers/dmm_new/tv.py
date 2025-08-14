import re

from pydantic import BaseModel, Field


def fanza_tv_payload(cid: str):
    return {
        "operationName": "FetchFanzaTvPlusContent",
        "variables": {
            "id": cid,
            "device": "BROWSER",
            "playDevice": "BROWSER",
            "isLoggedIn": False,
            "isForeign": False,
            "withResume": False,
        },
        "query": """query FetchFanzaTvPlusContent($id: ID!, $device: Device!, $isLoggedIn: Boolean!, $playDevice: PlayDevice!, $withResume: Boolean!, $isForeign: Boolean) {\n  fanzaTvPlus(device: $device) {\n    content(id: $id, isForeign: $isForeign) {\n      id\n      contentType\n      productId\n      shopName\n      shopOption\n      shopType\n      title\n      description(format: HTML)\n      packageImage\n      packageLargeImage\n      noIndex\n      ppvShopName\n      isFanzaTvPlusOnly\n      startDeliveryAt\n      endDeliveryAt\n      isBeingDelivered\n      deliveryStatus\n      sampleMovie {\n        url\n        thumbnail\n      }\n      samplePictures {\n        image\n        imageLarge\n      }\n      actresses {\n        name\n      }\n      histrions {\n        name\n      }\n      directors {\n        name\n      }\n      series {\n        name\n      }\n      maker {\n        name\n      }\n      label {\n        name\n      }\n      genres {\n        name\n      }\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n      }\n      hasBookmark @include(if: $isLoggedIn)\n      viewingRights(device: $playDevice) @include(if: $isLoggedIn) {\n        isStreamable\n      }\n      playInfo(withResume: $withResume, device: $device) {\n        duration\n        resumePartNumber\n        highestQualityName\n        parts {\n          contentId\n          number\n          resumePoint\n          duration\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}""",
    }


class Item(BaseModel):
    name: str = ""


class SampleMovie(BaseModel):
    url: str = ""
    thumbnail: str = ""


class SamplePicture(BaseModel):
    image: str = ""
    imageLarge: str = ""


class ReviewSummary(BaseModel):
    averagePoint: float = 0.0
    reviewerCount: int = 0
    reviewCommentCount: int = 0


class PlayInfoPart(BaseModel):
    contentId: str = ""
    number: int = 1
    resumePoint: int = 0
    duration: int = 0


class PlayInfo(BaseModel):
    duration: int = 0
    resumePartNumber: int = 1
    highestQualityName: str = ""
    parts: list[PlayInfoPart] = []


class FanzaSvodContent(BaseModel):
    id: str = ""
    contentType: str = ""
    productId: str = ""
    shopName: str = ""
    shopOption: str | None = None
    shopType: str = ""
    title: str = ""
    description: str = ""
    packageImage: str = ""
    packageLargeImage: str = ""
    noIndex: bool = False
    ppvShopName: str = ""
    isFanzaTvPlusOnly: bool = False
    startDeliveryAt: str = ""
    endDeliveryAt: str = ""
    isBeingDelivered: bool = False
    deliveryStatus: str = ""
    sampleMovie: SampleMovie = SampleMovie()
    samplePictures: list[SamplePicture] = []
    actresses: list[Item] = []
    histrions: list[dict] = []
    directors: list[Item] = []
    series: Item = Item()
    maker: Item = Item()
    label: Item = Item()
    genres: list[Item] = []
    reviewSummary: ReviewSummary = ReviewSummary()
    playInfo: PlayInfo = PlayInfo()


class FanzaTvPlus(BaseModel):
    content: FanzaSvodContent = FanzaSvodContent()


class _FanzaData(BaseModel):
    fanzaTvPlus: FanzaTvPlus = FanzaTvPlus()


class FanzaResp(BaseModel):
    data: _FanzaData = _FanzaData()


def dmm_tv_com_payload(season_id):
    data = {
        "operationName": "FetchVideo",
        "variables": {
            "seasonId": season_id,
            "device": "BROWSER",
            "playDevice": "BROWSER",
            "isLoggedIn": False,
        },
        "query": "query FetchVideo($seasonId: ID!, $device: Device!, $playDevice: PlayDevice!, $isLoggedIn: Boolean!, $purchasedFirst: Int, $purchasedAfter: String) {\n  video(id: $seasonId) {\n    id\n    __typename\n    seasonType\n    seasonName\n    hasBookmark @include(if: $isLoggedIn)\n    titleName\n    highlight(format: HTML)\n    description(format: HTML)\n    notices(format: HTML)\n    packageImage\n    productionYear\n    isNewArrival\n    customTag\n    isPublic\n    isExclusive\n    isBeingDelivered\n    viewingTypes\n    copyright\n    url\n    startPublicAt\n    campaign {\n      id\n      name\n      endAt\n      isLimitedPremium\n      __typename\n    }\n    rating {\n      category\n      __typename\n    }\n    casts {\n      castName\n      actorName\n      person {\n        id\n        __typename\n      }\n      __typename\n    }\n    staffs {\n      roleName\n      staffName\n      person {\n        id\n        __typename\n      }\n      __typename\n    }\n    categories {\n      id\n      name\n      __typename\n    }\n    genres {\n      id\n      name\n      __typename\n    }\n    relatedItems(device: $device) {\n      videos {\n        seasonId\n        video {\n          id\n          titleName\n          packageImage\n          isNewArrival\n          viewingTypes\n          customTag\n          isExclusive\n          rating {\n            category\n            __typename\n          }\n          ... on VideoSeason {\n            priceSummary {\n              lowestPrice\n              highestPrice\n              discountedLowestPrice\n              isLimitedPremium\n              __typename\n            }\n            __typename\n          }\n          ... on VideoLegacySeason {\n            priceSummary {\n              lowestPrice\n              highestPrice\n              discountedLowestPrice\n              isLimitedPremium\n              __typename\n            }\n            __typename\n          }\n          ... on VideoStageSeason {\n            priceSummary {\n              lowestPrice\n              highestPrice\n              discountedLowestPrice\n              isLimitedPremium\n              __typename\n            }\n            __typename\n          }\n          ... on VideoShortSeason {\n            priceSummary {\n              lowestPrice\n              highestPrice\n              discountedLowestPrice\n              isLimitedPremium\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      books {\n        seriesId\n        title\n        thumbnail\n        url\n        __typename\n      }\n      mono {\n        banner\n        url\n        __typename\n      }\n      scratch {\n        banner\n        url\n        __typename\n      }\n      onlineCrane {\n        banner\n        url\n        __typename\n      }\n      __typename\n    }\n    ... on VideoSeason {\n      metaDescription: description(format: PLAIN)\n      keyVisualImage\n      keyVisualWithoutLogoImage\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n        __typename\n      }\n      relatedSeasons {\n        id\n        title\n        __typename\n      }\n      nextDeliveryEpisode {\n        isBeforeDelivered\n        startDeliveryAt\n        __typename\n      }\n      continueWatching @include(if: $isLoggedIn) {\n        ...BaseContinueWatchingContent\n        __typename\n      }\n      priceSummary {\n        lowestPrice\n        highestPrice\n        discountedLowestPrice\n        isLimitedPremium\n        __typename\n      }\n      purchasedContents(first: $purchasedFirst, after: $purchasedAfter) @include(if: $isLoggedIn) {\n        total\n        edges {\n          node {\n            ...VideoSeasonContent\n            __typename\n          }\n          __typename\n        }\n        pageInfo {\n          endCursor\n          hasNextPage\n          __typename\n        }\n        __typename\n      }\n      svodEndDeliveryAt\n      __typename\n    }\n    ... on VideoLegacySeason {\n      metaDescription: description(format: PLAIN)\n      packageLargeImage\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n        __typename\n      }\n      sampleMovie {\n        url\n        thumbnail\n        __typename\n      }\n      samplePictures {\n        image\n        imageLarge\n        __typename\n      }\n      reviewSummary {\n        averagePoint\n        __typename\n      }\n      priceSummary {\n        lowestPrice\n        highestPrice\n        discountedLowestPrice\n        isLimitedPremium\n        __typename\n      }\n      continueWatching @include(if: $isLoggedIn) {\n        partNumber\n        ...BaseContinueWatchingContent\n        __typename\n      }\n      content {\n        ...VideoLegacySeasonContent\n        __typename\n      }\n      series {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    ... on VideoStageSeason {\n      metaDescription: description(format: PLAIN)\n      keyVisualImage\n      keyVisualWithoutLogoImage\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n        __typename\n      }\n      priceSummary {\n        lowestPrice\n        highestPrice\n        discountedLowestPrice\n        isLimitedPremium\n        __typename\n      }\n      allPerformances {\n        performanceDate\n        contents {\n          ...VideoStageSeasonContent\n          __typename\n        }\n        __typename\n      }\n      purchasedContents(first: $purchasedFirst, after: $purchasedAfter) @include(if: $isLoggedIn) {\n        total\n        edges {\n          node {\n            ...VideoStageSeasonContent\n            __typename\n          }\n          __typename\n        }\n        pageInfo {\n          endCursor\n          hasNextPage\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ... on VideoSpotLiveSeason {\n      metaDescription: description(format: PLAIN)\n      titleName\n      keyVisualImage\n      keyVisualWithoutLogoImage\n      __typename\n    }\n    ... on VideoShortSeason {\n      metaDescription: description(format: PLAIN)\n      keyVisualImage\n      keyVisualWithoutLogoImage\n      reviewSummary {\n        averagePoint\n        reviewerCount\n        reviewCommentCount\n        __typename\n      }\n      relatedSeasons {\n        id\n        title\n        __typename\n      }\n      nextDeliveryEpisode {\n        isBeforeDelivered\n        startDeliveryAt\n        __typename\n      }\n      continueWatching @include(if: $isLoggedIn) {\n        ...BaseContinueWatchingContent\n        __typename\n      }\n      priceSummary {\n        lowestPrice\n        highestPrice\n        discountedLowestPrice\n        isLimitedPremium\n        __typename\n      }\n      purchasedContents(first: $purchasedFirst, after: $purchasedAfter) @include(if: $isLoggedIn) {\n        total\n        edges {\n          node {\n            ...VideoSeasonContent\n            __typename\n          }\n          __typename\n        }\n        pageInfo {\n          endCursor\n          hasNextPage\n          __typename\n        }\n        __typename\n      }\n      svodEndDeliveryAt\n      __typename\n    }\n  }\n}\n\nfragment BaseContinueWatchingContent on VideoContinueWatching {\n  id\n  resumePoint\n  contentId\n  content {\n    id\n    episodeTitle\n    episodeNumberName\n    episodeNumber\n    episodeImage\n    drmLevel {\n      hasStrictProtection\n      __typename\n    }\n    viewingRights(device: $playDevice) {\n      isStreamable\n      isDownloadable\n      __typename\n    }\n    ppvProducts {\n      id\n      isBeingDelivered\n      isBundleParent\n      isOnSale\n      price {\n        price\n        salePrice\n        isLimitedPremium\n        __typename\n      }\n      __typename\n    }\n    svodProduct {\n      contentId\n      isBeingDelivered\n      __typename\n    }\n    freeProduct {\n      contentId\n      isBeingDelivered\n      __typename\n    }\n    priceSummary {\n      campaignId\n      lowestPrice\n      highestPrice\n      discountedLowestPrice\n      isLimitedPremium\n      __typename\n    }\n    ppvExpiration {\n      startDeliveryAt\n      expirationType\n      viewingExpiration\n      viewingStartExpiration\n      __typename\n    }\n    playInfo {\n      contentId\n      resumePartNumber\n      parts {\n        number\n        duration\n        contentId\n        resume {\n          point\n          isCompleted\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment VideoSeasonContent on VideoContent {\n  id\n  seasonId\n  episodeTitle\n  episodeNumberName\n  episodeNumber\n  episodeImage\n  episodeDetail\n  sampleMovie\n  contentType\n  drmLevel {\n    hasStrictProtection\n    __typename\n  }\n  viewingRights(device: $playDevice) {\n    isStreamable\n    isDownloadable\n    downloadableFiles @include(if: $isLoggedIn) {\n      totalFileSize\n      quality {\n        name\n        displayName\n        displayPriority\n        __typename\n      }\n      parts {\n        partNumber\n        fileSize\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  ppvProducts {\n    id\n    isPurchased @include(if: $isLoggedIn)\n    isBeingDelivered\n    isBundleParent\n    isOnSale\n    price {\n      price\n      salePrice\n      isLimitedPremium\n      __typename\n    }\n    __typename\n  }\n  svodProduct {\n    contentId\n    isBeingDelivered\n    startDeliveryAt\n    __typename\n  }\n  freeProduct {\n    contentId\n    isBeingDelivered\n    __typename\n  }\n  priceSummary {\n    campaignId\n    lowestPrice\n    highestPrice\n    discountedLowestPrice\n    isLimitedPremium\n    __typename\n  }\n  ppvExpiration @include(if: $isLoggedIn) {\n    startDeliveryAt\n    expirationType\n    viewingExpiration\n    viewingStartExpiration\n    __typename\n  }\n  playInfo {\n    contentId\n    duration\n    textRenditions\n    audioRenditions\n    highestQuality\n    isSupportHDR\n    highestAudioChannelLayout\n    resumePartNumber @include(if: $isLoggedIn)\n    parts {\n      number\n      duration\n      contentId\n      resume @include(if: $isLoggedIn) {\n        point\n        isCompleted\n        __typename\n      }\n      __typename\n    }\n    tags\n    __typename\n  }\n  __typename\n}\n\nfragment VideoLegacySeasonContent on VideoContent {\n  id\n  contentType\n  episodeTitle\n  episodeNumberName\n  vrSampleMovie {\n    url\n    __typename\n  }\n  ppvProducts {\n    id\n    isPurchased @include(if: $isLoggedIn)\n    isBeingDelivered\n    isOnSale\n    price {\n      price\n      salePrice\n      isLimitedPremium\n      __typename\n    }\n    __typename\n  }\n  svodProduct {\n    contentId\n    isBeingDelivered\n    startDeliveryAt\n    __typename\n  }\n  freeProduct {\n    contentId\n    isBeingDelivered\n    __typename\n  }\n  priceSummary {\n    lowestPrice\n    highestPrice\n    discountedLowestPrice\n    isLimitedPremium\n    __typename\n  }\n  ppvExpiration @include(if: $isLoggedIn) {\n    startDeliveryAt\n    expirationType\n    viewingExpiration\n    viewingStartExpiration\n    __typename\n  }\n  viewingRights(device: $playDevice) {\n    isStreamable\n    isDownloadable\n    downloadableFiles @include(if: $isLoggedIn) {\n      totalFileSize\n      quality {\n        name\n        displayName\n        displayPriority\n        __typename\n      }\n      parts {\n        partNumber\n        fileSize\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  drmLevel {\n    hasStrictProtection\n    __typename\n  }\n  playInfo {\n    contentId\n    duration\n    highestQuality\n    isSupportHDR\n    highestAudioChannelLayout\n    textRenditions\n    audioRenditions\n    resumePartNumber @include(if: $isLoggedIn)\n    parts {\n      number\n      duration\n      contentId\n      resume @include(if: $isLoggedIn) {\n        point\n        isCompleted\n        __typename\n      }\n      __typename\n    }\n    tags\n    __typename\n  }\n  __typename\n}\n\nfragment VideoStageSeasonContent on VideoContent {\n  id\n  seasonId\n  episodeTitle\n  episodeNumberName\n  episodeNumber\n  episodeImage\n  episodeDetail\n  sampleMovie\n  contentType\n  priority\n  drmLevel {\n    hasStrictProtection\n    __typename\n  }\n  viewingRights(device: $playDevice) {\n    isStreamable\n    isDownloadable\n    downloadableFiles @include(if: $isLoggedIn) {\n      totalFileSize\n      quality {\n        name\n        displayName\n        displayPriority\n        __typename\n      }\n      parts {\n        partNumber\n        fileSize\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  ppvProducts {\n    id\n    contentId\n    isPurchased @include(if: $isLoggedIn)\n    isBeingDelivered\n    isOnSale\n    isBundleParent\n    price {\n      price\n      salePrice\n      isLimitedPremium\n      __typename\n    }\n    __typename\n  }\n  svodProduct {\n    contentId\n    isBeingDelivered\n    startDeliveryAt\n    __typename\n  }\n  freeProduct {\n    contentId\n    isBeingDelivered\n    __typename\n  }\n  priceSummary {\n    campaignId\n    lowestPrice\n    highestPrice\n    discountedLowestPrice\n    isLimitedPremium\n    __typename\n  }\n  ppvExpiration @include(if: $isLoggedIn) {\n    startDeliveryAt\n    expirationType\n    viewingExpiration\n    viewingStartExpiration\n    __typename\n  }\n  playInfo {\n    contentId\n    duration\n    textRenditions\n    audioRenditions\n    highestQuality\n    isSupportHDR\n    highestAudioChannelLayout\n    resumePartNumber @include(if: $isLoggedIn)\n    parts {\n      number\n      duration\n      contentId\n      resume @include(if: $isLoggedIn) {\n        point\n        isCompleted\n        __typename\n      }\n      __typename\n    }\n    tags\n    __typename\n  }\n  __typename\n}\n",
    }

    return data


class VideoRating(BaseModel):
    category: str = ""


class Cast(BaseModel):
    castName: str = ""
    actorName: str = ""


class Staff(BaseModel):
    roleName: str = ""
    staffName: str = ""


class VideoSeason(BaseModel):
    id: str = ""
    seasonType: str = ""
    seasonName: str = ""
    titleName: str = ""
    highlight: str | None = None
    description: str = ""
    notices: str | None = None
    packageImage: str = ""
    productionYear: int = 0
    isNewArrival: bool = False
    customTag: str = ""
    url: str = ""
    startPublicAt: str = ""
    campaign: str | None = None
    rating: VideoRating = Field(default_factory=VideoRating)
    casts: list[Cast] = []
    staffs: list[Staff] = []
    categories: list[Item] = []
    genres: list[Item] = []
    metaDescription: str = ""
    keyVisualImage: str = ""
    keyVisualWithoutLogoImage: str = ""
    reviewSummary: ReviewSummary = Field(default_factory=ReviewSummary)
    priceSummary: str | None = None
    svodEndDeliveryAt: str | None = None


class VideoData(BaseModel):
    video: VideoSeason = Field(default_factory=VideoSeason)


class DmmTvResponse(BaseModel):
    data: VideoData = Field(default_factory=VideoData)


def parse_fanza_resp(resp: FanzaResp):
    api_data = resp.data.fanzaTvPlus.content
    title = api_data.title
    outline = api_data.description
    actors = [actress.name for actress in api_data.actresses]
    actor = ",".join(actors)
    poster_url = api_data.packageImage
    cover_url = api_data.packageLargeImage
    tags = [genre.name for genre in api_data.genres]
    tag = ",".join(tags)
    runtime = str(int(api_data.playInfo.duration / 60))
    score = str(api_data.reviewSummary.averagePoint)
    series = api_data.series.name
    directors = api_data.directors
    studio = api_data.maker.name

    publisher = api_data.label.name

    extrafanart = []
    for sample_pic in api_data.samplePictures:
        if sample_pic.imageLarge:
            extrafanart.append(sample_pic.imageLarge)

    # https://cc3001.dmm.co.jp/hlsvideo/freepv/s/ssi/ssis00497/playlist.m3u8
    trailer_url = api_data.sampleMovie.url.replace("hlsvideo", "litevideo")
    cid_match = re.search(r"/([^/]+)/playlist.m3u8", trailer_url)
    if cid_match:
        cid = cid_match.group(1)
        trailer = trailer_url.replace("playlist.m3u8", cid + "_sm_w.mp4")
    else:
        trailer = ""
    return (
        True,
        title,
        outline,
        actor,
        poster_url,
        cover_url,
        tag,
        runtime,
        score,
        series,
        directors,
        studio,
        publisher,
        extrafanart,
        trailer,
        "",
    )
