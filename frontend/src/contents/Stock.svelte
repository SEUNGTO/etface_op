<script>
    import {
        Li,
        Table,
        TableBody,
        TableBodyCell,
        TableBodyRow,
        TableHead,
        TableHeadCell,
        TableSearch,
    } from "flowbite-svelte";
    import { Range, Label } from "flowbite-svelte";
    import { Tabs, TabItem } from "flowbite-svelte";
    import { AccordionItem, Accordion } from "flowbite-svelte";
    import { Timeline, TimelineItem, Button } from "flowbite-svelte";
    import { Dropdown, Checkbox } from "flowbite-svelte";
    import { ChevronDownOutline } from "flowbite-svelte-icons";
    import { Alert, List } from "flowbite-svelte";
    import { P, Span } from "flowbite-svelte";
    import { Spinner } from "flowbite-svelte";
    import { Heading } from "flowbite-svelte";
    import { InfoCircleSolid, NewspaperSolid, MessageDotsSolid } from 'flowbite-svelte-icons';

    import Line from "/components/Line.svelte";
    import { onMount } from "svelte";
    import { DividerHorizontal } from "svelte-radix";

    export let code;
    export let name;
    export let type;

    const get_entire_new = async () => {
        const url = `http://43.201.252.164/entire/new`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_entire_drop = async () => {
        const url = `http://43.201.252.164/entire/drop`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_research_data = async () => {
        const url = `http://43.201.252.164/${type}/research/${code}`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };
    const get_news_data = async () => {
        const url = `http://43.201.252.164/${type}/news/${code}`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_telegram_data = async () => {
        const url = `http://43.201.252.164/${type}/telegram/${code}`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_data_by_order = async (order) => {
        const url = `http://43.201.252.164/${type}/${code}/${order}`;
        const response = await fetch(url);
        const top10 = await response.json();
        return top10;
    };
    const get_price_data = async () => {
        const url = `http://43.201.252.164/${type}/${code}/price`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };
    const get_price_describe_data = async () => {
        const url = `http://43.201.252.164/${type}/${code}/price/describe`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    // base section
    let entireNewData = {};
    let entireNew = [];
    let entireDropData = {};
    let entireDrop = [];
    let searchNewNum = 10;
    let searchDropNum = 10;

    let newetfSearchTerm = "";
    $: filteredETFNews = entireNew
        .filter(
            (item) =>
                item["ETF"]
                    .toLowerCase()
                    .indexOf(newetfSearchTerm.toLowerCase()) !== -1,
        )
        .slice(0, searchNewNum);

    let dropetfSearchTerm = "";
    $: filteredETFDrops = entireDrop
        .filter(
            (item) =>
                item["ETF"].toLowerCase().indexOf(dropetfSearchTerm) !== -1,
        )
        .slice(0, searchDropNum);
    // 1번 섹션
    let researchData = {};
    let research = [];
    let researchMsg = [];
    let searchTerm = "";
    $: filteredResearchs = research.filter(
        (item) =>
            item["증권사"].toLowerCase().indexOf(searchTerm.toLowerCase()) !==
            -1,
    );

    let newsData = {};
    let news = [];

    let telegramData = {};
    let telegramItems = [];

    let channels = [
        "주식 급등일보🚀급등테마·대장주 탐색기",
        "핀터 - 국내공시 6줄 요약",
        "AWAKE-일정, 테마, 이벤트드리븐",
        "52주 신고가 모니터링",
        "SB 리포트 요약",
    ];
    let filteredChannel = ["주식 급등일보🚀급등테마·대장주 탐색기"];
    $: renderChannel = telegramItems.filter(
        (channels) => filteredChannel.indexOf(channels["채널명"]) !== -1,
    );

    // 2번 섹션
    let priceData = get_price_data();
    let priceDescData = {};

    // 3번 섹션
    let largeRatioData = {};
    let largeRatio = [];

    let increaseData = {};
    let increase = [];

    let decreaseData = {};
    let decrease = [];

    let newStockData = {};
    let newStock = [];

    let dropStockData = {};
    let dropStock = [];

    onMount(async () => {
        entireNewData = await get_entire_new();
        entireNew = JSON.parse(entireNewData.data);
        entireDropData = await get_entire_drop();
        entireDrop = JSON.parse(entireDropData.data);

        researchData = await get_research_data();
        research = JSON.parse(researchData.data);
        researchMsg = researchData.message;

        newsData = await get_news_data();
        news = JSON.parse(newsData.data);

        priceDescData = await get_price_describe_data();

        largeRatioData = await get_data_by_order("largeRatio");
        largeRatio = JSON.parse(largeRatioData);

        increaseData = await get_data_by_order("increase");
        increase = JSON.parse(increaseData);

        decreaseData = await get_data_by_order("decrease");
        decrease = JSON.parse(decreaseData);

        newStockData = await get_data_by_order("new");
        newStock = JSON.parse(newStockData);

        dropStockData = await get_data_by_order("drop");
        dropStock = JSON.parse(dropStockData);

        telegramData = await get_telegram_data();
        telegramItems = JSON.parse(telegramData);
    });
</script>

<section>
    <div class="py-5">
        <Accordion>
            <AccordionItem>
                <span slot="header"> ✅ ETF가 새로 산 종목들</span>
                {#await entireNewData}
                    ETF가 새로 산 종목들 기다리는 중
                {:then entrNew}
                    <div class="overflow-hidden hover:overflow-auto max-h-96">
                        <Label>최대 검색 개수 : {searchNewNum}개</Label>
                        <Range
                            id="range-search-num"
                            min="1"
                            max="100"
                            bind:value={searchNewNum}
                        />
                        <Table shadow>
                            <TableSearch
                                placeholder="ETF명 검색"
                                hoverable={true}
                                bind:inputValue={newetfSearchTerm}
                            >
                                <TableHead>
                                    <TableHeadCell>ETF</TableHeadCell>
                                    <TableHeadCell>종목코드</TableHeadCell>
                                    <TableHeadCell>종목명</TableHeadCell>
                                    <TableHeadCell>보유량</TableHeadCell>
                                    <TableHeadCell>보유금액</TableHeadCell>
                                    <TableHeadCell>비중</TableHeadCell>
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each filteredETFNews as item}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{item["ETF"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "종목코드"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["종목명"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["보유량"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "보유금액"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["비중"]}</TableBodyCell
                                            >
                                        </TableBodyRow>
                                    {/each}
                                </TableBody>
                            </TableSearch>
                        </Table>
                    </div>
                {/await}
            </AccordionItem>
            <AccordionItem>
                <span slot="header"> ⚠ ETF가 모두 판 종목들</span>
                {#await entireDropData}
                    "ETF가 모두 판 종목들 기다리는 중"
                {:then entrDrp}
                    <div class="overflow-hidden hover:overflow-auto max-h-96">
                        <Label>최대 검색 개수 : {searchDropNum}개</Label>
                        <Range
                            id="range-search-num"
                            min="1"
                            max="100"
                            bind:value={searchDropNum}
                        />
                        <Table shadow>
                            <TableSearch
                                placeholder="ETF명 검색"
                                hoverable={true}
                                bind:inputValue={dropetfSearchTerm}
                            >
                                <TableHead>
                                    <TableHeadCell>ETF</TableHeadCell>
                                    <TableHeadCell>종목코드</TableHeadCell>
                                    <TableHeadCell>종목명</TableHeadCell>
                                    <TableHeadCell>보유량</TableHeadCell>
                                    <TableHeadCell>보유금액</TableHeadCell>
                                    <TableHeadCell>비중</TableHeadCell>
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each filteredETFDrops as item}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{item["ETF"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "종목코드"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["종목명"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["보유량"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "보유금액"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["비중"]}</TableBodyCell
                                            >
                                        </TableBodyRow>
                                    {/each}
                                </TableBody>
                            </TableSearch>
                        </Table>
                    </div>
                {/await}
            </AccordionItem>
        </Accordion>
    </div>
</section>

<section>
    <div class="py-10">
        <Heading tag="h3"> 1. {name}에 대해 이런 이야기들이 있어요</Heading>
        <div class="py-4">
            <Tabs
            tabStyle = "underline"
            >
                <TabItem
                    open
                    title="증권사 리포트"
                    activeClasses = 'p-4 font-bold text-red-500 border-red-600 border-b-2 rounded-t-lg dark:bg-gray-800 dark:text-primary-500'
                    inactiveClasses = "p-4 text-black-500 bg-grey-600 dark:text-gray-400 bg-grey-700"
                >
                    {#await researchData}
                        "비중 늘어난 종목 기다리는 중"
                    {:then rsch}
                        {#if researchMsg['length'] == 0}
                            <Alert color="red" border>
                                ❌ 최근 6개월 동안 {name}에 대한 리포트가 없어요.
                            </Alert>
                        {:else}
                            <div>
                                {#await researchData}
                                    메세지 기다리는 중
                                {:then rsch}
                                    <Alert color="green" border>
                                        <InfoCircleSolid slot="icon" class="w-5 h-5" />
                                        최근 6개월 동안 <strong>{name}</strong>에 대해 총 <strong>{researchMsg["length"]}개</strong>의 리포트가 나왔어요.
                                    </Alert>
                                    <Alert class = !items-start color="dark">
                                        <List class="mt-1.5 ms-4">
                                            <P whitespace = "preline">
                                                ◾ {name}에 대해 증권사들은 평균 <Span underline decorationClass="decoration-grey-500 decoration-double">{researchMsg['avgPrice']}원</Span>을 제시했어요.
                                                ◾ 가장 높은 목표가는 <strong>{researchMsg["maxResearcher"]}</strong>이 제시한 <Span underline decorationClass="decoration-red-500 decoration-double">{researchMsg["maxPrice"]}원</Span>이에요.
                                                ◾ 가장 낮은 목표가는 <strong>{researchMsg["minResearcher"]}</strong>이 제시한 <Span underline decorationClass="decoration-blue-500 decoration-double">{researchMsg["minPrice"]}원</Span>이에요.
                                            </P>
                                        </List>
                                    </Alert>

                                {/await}
                            </div>
                            <div class="overflow-hidden hover:overflow-auto max-h-96">
                                <Table shadow>
                                    <TableSearch
                                        placeholder="증권사명 검색"
                                        hoverable={true}
                                        bind:inputValue={searchTerm}
                                    >
                                        <TableHead>
                                            <TableHeadCell
                                                >리포트 제목</TableHeadCell
                                            >
                                            <TableHeadCell>목표가</TableHeadCell>
                                            <TableHeadCell>의견</TableHeadCell>
                                            <TableHeadCell>게시일자</TableHeadCell>
                                            <TableHeadCell>증권사</TableHeadCell>
                                            <TableHeadCell>링크</TableHeadCell>
                                        </TableHead>
                                        <TableBody tableBodyClass="divide-y">
                                            {#each filteredResearchs as item}
                                                <TableBodyRow>
                                                    <TableBodyCell
                                                        >{item[
                                                            "리포트 제목"
                                                        ]}</TableBodyCell
                                                    >
                                                    <TableBodyCell
                                                        >{item[
                                                            "목표가"
                                                        ]}</TableBodyCell
                                                    >
                                                    <TableBodyCell
                                                        >{item[
                                                            "의견"
                                                        ]}</TableBodyCell
                                                    >
                                                    <TableBodyCell
                                                        >{item[
                                                            "게시일자"
                                                        ]}</TableBodyCell
                                                    >
                                                    <TableBodyCell
                                                        >{item[
                                                            "증권사"
                                                        ]}</TableBodyCell
                                                    >
                                                    <TableBodyCell>
                                                        <a
                                                            href={item["링크"]}
                                                            target="_blank"
                                                            class="font-medium text-primary-600 hover:underline dark:text-primary-500"
                                                            >🔗</a
                                                        >
                                                    </TableBodyCell>
                                                </TableBodyRow>
                                            {/each}
                                        </TableBody>
                                    </TableSearch>
                                </Table>
                            </div>
                        {/if}   

                    {/await}
                </TabItem>
                <TabItem
                    title="뉴스"
                    activeClasses = 'p-4 font-bold text-red-500 border-red-600 border-b-2 rounded-t-lg dark:bg-gray-800 dark:text-primary-500'
                    inactiveClasses = "p-4 text-black-500 bg-grey-600 dark:text-gray-400 bg-grey-700"
                >
                    {#await newsData}
                        "뉴스 데이터 검색하는 중"
                    {:then nws}
                        <Alert color="green" border
                            >
                            <NewspaperSolid slot="icon" class="w-5 h-5" />
                            방금 네이버 뉴스에서 <strong>{name}</strong>을 검색해왔어요.</Alert
                        >
                        <div class="overflow-hidden hover:overflow-auto max-h-96">
                            <Table shadow>
                                <TableHead>
                                    <TableHeadCell>기사 제목</TableHeadCell>
                                    <TableHeadCell>날짜</TableHeadCell>
                                    <TableHeadCell>링크</TableHeadCell>
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each news as nn}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{nn[
                                                    "기사 제목"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{nn["날짜"]}</TableBodyCell
                                            >
                                            <TableBodyCell>
                                                <a
                                                    href={nn["링크"]}
                                                    target="_blank"
                                                    class="font-medium text-primary-600 hover:underline dark:text-primary-500"
                                                    >🔗</a
                                                >
                                            </TableBodyCell>
                                        </TableBodyRow>
                                    {/each}
                                </TableBody>
                            </Table>
                        </div>
                    {/await}
                </TabItem>
                <TabItem
                    title="텔레그램"
                    activeClasses = 'p-4 font-bold text-red-500 border-red-600 border-b-2 rounded-t-lg dark:bg-gray-800 dark:text-primary-500'
                    inactiveClasses = "p-4 text-black-500 bg-grey-600 dark:text-gray-400 bg-grey-700"
                >
                    {#if Object.keys(telegramData).length == 0}
                        <Alert color="blue">
                            <Spinner
                                class="me-3"
                                size="8"
                                color="alternative"
                            />
                            텔레그램 메세지를 모으고 있어요.
                        </Alert>
                    {:else}
                        <Alert color="green" border>
                        <MessageDotsSolid slot="icon" class="w-5 h-5" />
                        텔레그램에서 <strong>{name}</strong> 소식을 모아왔어요.
                        </Alert>

                        <div class="flex gap-2">
                            <Button color="alternative"
                                >확인하고 싶은 채널<ChevronDownOutline
                                    class="w-6 h-6 ms-2 text-black dark:text-white"
                                /></Button
                            >
                            <Dropdown
                                class="overflow-y-auto px-3 pb-3 text-sm h-44"
                            >
                                {#each channels as channel, index}
                                    <li
                                        class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
                                    >
                                        <Checkbox
                                            bind:group={filteredChannel}
                                            value={channel}>{channel}</Checkbox
                                        >
                                    </li>
                                {/each}
                            </Dropdown>
                        </div>
                        <div class="overflow-hidden hover:overflow-auto h-96">
                            <Timeline>
                                {#each renderChannel as item}
                                    <TimelineItem
                                    class = 'px-4'
                                        title={item["채널명"]}
                                        date={item["시간"]}
                                    >
                                        <p>
                                            {item["종목명"]}에 관한 이야기에요.
                                            (링크 :<a
                                                href={item["링크"]}
                                                target="_blank">🔗</a
                                            >)
                                        </p>
                                        <p
                                            class="mb-4 text-base font-normal text-gray-500 dark:text-gray-400"
                                        >
                                            {item["메세지"]}
                                        </p>
                                    </TimelineItem>
                                {/each}
                            </Timeline>
                        </div>
                    {/if}
                </TabItem>
            </Tabs>
        </div>
    </div>
</section>
<section>
    <Heading tag="h3">2. {name}의 최근 세 달 주가 추이에요.</Heading>
    <div class = 'py-4 flex justify-items-stretch gap-2'>
        {#await priceDescData}
        "분석데이터 기다리는 중"
        {:then desc}

        {#if type == 'Stock' & researchMsg['length'] != 0}
        <Alert class = 'py-4'color="dark" border>
            ✅ 평균 목표가({researchMsg['avgPrice']}원) 대비 현재 종가는 {priceDescData['target_ratio']}% 수준이에요.
            <P whitespace = "preline">
            ◾ 만일 {priceDescData['to_target']}% 상승한다면 증권사들의 평균 목표가에 도달해요.
            </P>
        </Alert>
        {/if}
        <Alert class = 'py-4' color="red" border>
            🟥 지난 세 달 중에 최고가는 {priceDescData['highest']}원이에요. 
            <P whitespace = "preline">
                ◾ 현재 종가 대비 {priceDescData['highest_ratio']}% 높아요.
            </P>
        </Alert>
        <Alert class = 'py-2'color="blue" border>
            🟦 지난 세 달 중에 최저가는 {priceDescData['lowest']}원이에요. 
            <P whitespace = "preline">
            ◾ 현재 종가 대비 {priceDescData['lowest_ratio']}% 낮아요.
            </P>
        </Alert>
        {/await}
    </div>
    
    <div id="plot-price">
        {#await priceData}
            "top10 data를 기다리는 중"
        {:then price}
            <Line {price} />
        {/await}
    </div>
</section>

<section>
    <div class="py-10">
        <Heading tag="h3"
            >3. {name}에 관심을 갖고 있는 ETF들이에요.</Heading
        >
        <div class="py-5">
            <Heading tag="h5">💡 {name}의 비중이 높은 ETF들이에요.</Heading>
            {#await largeRatioData}
                "비중 늘어난 종목 기다리는 중"
            {:then lr}
                <div class="overflow-hidden hover:overflow-auto max-h-96">
                    <Table shadow>
                        <TableHead>
                            <TableHeadCell>ETF</TableHeadCell>
                            <TableHeadCell>최근 비중(%)</TableHeadCell>
                            <TableHeadCell>일주일 전 비중(%)</TableHeadCell>
                            <TableHeadCell>차이(%p)</TableHeadCell>
                        </TableHead>
                        <TableBody tableBodyClass="divide-y">
                            {#each largeRatio as item}
                                <TableBodyRow>
                                    <TableBodyCell>{item["ETF"]}</TableBodyCell>
                                    <TableBodyCell
                                        >{item["비중(기준일)"]}</TableBodyCell
                                    >
                                    <TableBodyCell
                                        >{item["비중(비교일)"]}</TableBodyCell
                                    >
                                    <TableBodyCell>{item["차이"]}</TableBodyCell
                                    >
                                </TableBodyRow>
                            {/each}
                        </TableBody>
                    </Table>
                </div>
            {/await}
        </div>
        <div class="py-10 grid grid-cols-2 gap-4">
            <div class="col-start-1">
                <Heading tag="h5">📈 최근 비중을 늘렸어요.</Heading>
                <div class="overflow-hidden hover:overflow-auto max-h-96">
                    {#await increaseData}
                        "비중 늘어난 종목 기다리는 중"
                    {:then inc}
                        <Table shadow>
                            <TableHead>
                                <TableHeadCell>ETF</TableHeadCell>
                                <TableHeadCell>최근 비중(%)</TableHeadCell>
                                <TableHeadCell>일주일 전 비중(%)</TableHeadCell>
                                <TableHeadCell>차이(%p)</TableHeadCell>
                            </TableHead>
                            <TableBody tableBodyClass="divide-y">
                                {#each increase as item}
                                    <TableBodyRow>
                                        <TableBodyCell>{item["ETF"]}</TableBodyCell>
                                        <TableBodyCell
                                            >{item["비중(기준일)"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["비중(비교일)"]}</TableBodyCell
                                        >
                                        <TableBodyCell>{item["차이"]}</TableBodyCell
                                        >
                                    </TableBodyRow>
                                {/each}
                            </TableBody>
                        </Table>
                    {/await}
                </div>
            </div>
            
            <div class="col-start-2">
                <Heading tag="h5">📉 최근 비중을 줄였어요.</Heading>
                <div class="overflow-hidden hover:overflow-auto max-h-96">
                    {#await decreaseData}
                        "비중 늘어난 종목 기다리는 중"
                    {:then dcr}
                        <Table shadow>
                            <TableHead>
                                <TableHeadCell>ETF</TableHeadCell>
                                <TableHeadCell>최근 비중(%)</TableHeadCell>
                                <TableHeadCell>일주일 전 비중(%)</TableHeadCell>
                                <TableHeadCell>차이(%p)</TableHeadCell>
                            </TableHead>
                            <TableBody tableBodyClass="divide-y">
                                {#each decrease as item}
                                    <TableBodyRow>
                                        <TableBodyCell>{item["ETF"]}</TableBodyCell>
                                        <TableBodyCell
                                            >{item["비중(기준일)"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["비중(비교일)"]}</TableBodyCell
                                        >
                                        <TableBodyCell>{item["차이"]}</TableBodyCell
                                        >
                                    </TableBodyRow>
                                {/each}
                            </TableBody>
                        </Table>
                    {/await}
                </div>
            </div>
            
        </div>
        <div class="py-10 grid grid-cols-2 gap-4">
            <div class="col-start-1">
                <Heading tag="h5">🆕 포트폴리오에 추가했어요.</Heading>
                <div class="overflow-hidden hover:overflow-auto max-h-96">

                    {#await newStockData}
                        "비중 늘어난 종목 기다리는 중"
                    {:then nw}
                        {#if newStock.length == 0}
                            <Alert color="blue">
                                <span class="font-medium"
                                    >최근에 {name}을 새로 산 ETF는 없어요.</span
                                >
                            </Alert>
                        {:else}
                            <Table shadow>
                                <TableHead>
                                    <TableHeadCell>ETF</TableHeadCell>
                                    <TableHeadCell
                                        >포트폴리오에 추가한 비중(%)</TableHeadCell
                                    >
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each newStock as item}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{item["ETF"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "비중(기준일)"
                                                ]}</TableBodyCell
                                            >
                                        </TableBodyRow>
                                    {/each}
                                </TableBody>
                            </Table>
                        {/if}
                    {/await}
                </div>
            </div>

            <div class="col-start-2">
                <Heading tag="h5">❎ 포트폴리오에서 제외했어요.</Heading>
                <div class="overflow-hidden hover:overflow-auto max-h-96">
                    {#await dropStockData}
                        "비중 늘어난 종목 기다리는 중"
                    {:then drp}
                        {#if dropStock.length == 0}
                            <Alert color="blue">
                                <span class="font-medium"
                                    >최근에 {name}을 모두 판 ETF는 없어요.</span
                                >
                            </Alert>
                        {:else}
                            <Table shadow>
                                <TableHead>
                                    <TableHeadCell>ETF</TableHeadCell>
                                    <TableHeadCell
                                        >포트폴리오에서 판매한 비중(%)</TableHeadCell
                                    >
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each dropStock as item}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{item["ETF"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "비중(비교일)"
                                                ]}</TableBodyCell
                                            >
                                        </TableBodyRow>
                                    {/each}
                                </TableBody>
                            </Table>
                        {/if}
                    {/await}
                </div>
            </div>
        </div>
    </div>
</section>

<style>
    #plot-price {
        margin: 1em;
        border-radius: 1em;
        padding-left: 5px;
        padding-right: 5px;
        padding-bottom: 5px;
        border: 1px solid lightgrey;
        max-width: 100%;
        max-height: 30vh;
        align-self: center;
        align-items: center;
    }
</style>
