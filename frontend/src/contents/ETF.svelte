<script>
    import {
        Table,
        TableBody,
        TableBodyCell,
        TableBodyRow,
        TableHead,
        TableHeadCell,
        TableSearch,
    } from "flowbite-svelte";
    import { Heading } from "flowbite-svelte";
    import { Spinner } from "flowbite-svelte";
    import { Alert } from "flowbite-svelte";
    import { P, Span} from "flowbite-svelte";
    import { Tabs, TabItem } from "flowbite-svelte";
    import { Range, Label } from "flowbite-svelte";
    import { AccordionItem, Accordion } from "flowbite-svelte";
    import { Timeline, TimelineItem, Button } from "flowbite-svelte";
    import { Dropdown, Checkbox } from "flowbite-svelte";
    import { ChevronDownOutline } from "flowbite-svelte-icons";
    import Pie from "/components/Pie.svelte";
    import Line from "/components/Line.svelte";
    import { onMount } from "svelte";

    export let code;
    export let name;
    export let type;

    const get_entire_new = async () => {
        const url = `http://43.201.252.164:8000/entire/new`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_entire_drop = async () => {
        const url = `http://43.201.252.164:8000/entire/drop`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_detail_data = async () => {
        const url = `http://43.201.252.164:8000/${type}/${code}/depositDetail`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_top10_data = async () => {
        const url = `http://43.201.252.164:8000/${type}/${code}/top10`;
        const response = await fetch(url);
        const top10 = await response.json();
        return top10;
    };

    const get_telegram_data = async () => {
        const url = `http://43.201.252.164:8000/${type}/telegram/${code}`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_price_data = async () => {
        const url = `http://43.201.252.164:8000/${type}/${code}/price`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };
    const get_price_describe_data = async () => {
        const url = `http://43.201.252.164:8000/${type}/${code}/price/describe`;
        const response = await fetch(url);
        const data = await response.json();
        return data;
    };

    const get_data_by_order = async (order) => {
        const url = `http://43.201.252.164:8000/${type}/${code}/${order}`;
        const response = await fetch(url);
        const top10 = await response.json();
        return top10;
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
                item["ETF"]
                    .toLowerCase()
                    .indexOf(dropetfSearchTerm.toLowerCase()) !== -1,
        )
        .slice(0, searchDropNum);

    // 1번 섹션 : 테이블 검색용
    let ETFDATA = {};
    let items = [];
    let searchTerm = "";
    $: filteredItems = items.filter(
        (item) =>
            item["종목명"].toLowerCase().indexOf(searchTerm.toLowerCase()) !==
            -1,
    );

    // 2번 섹션 : 텔레그램 등
    let telegramData = {};
    let telegramItems = [];

    let top5 = [];
    let channels = [
        "주식 급등일보🚀급등테마·대장주 탐색기",
        "핀터 - 국내공시 6줄 요약",
        "AWAKE-일정, 테마, 이벤트드리븐",
        "52주 신고가 모니터링",
        "SB 리포트 요약",
    ];
    let filteredChannel = ["주식 급등일보🚀급등테마·대장주 탐색기"];
    let filteredTop5 = [];

    $: renderChannel = telegramItems.filter(
        (channels) =>
            filteredChannel.indexOf(channels["채널명"]) !== -1 &&
            filteredTop5.indexOf(channels["종목명"]) !== -1,
    );

    // 3번 섹션
    let priceData = get_price_data()
    let priceDescData = {};

    // 4번~7번 섹션
    let increaseData = {};
    let increase = [];

    let decreaseData = {};
    let decrease = [];

    let newStockData = {};
    let newStock = [];

    let dropStockData = {};
    let dropStock = [];

    // (공통) 데이터 받기
    let top10Data = get_top10_data();

    onMount(async () => {
        entireNewData = await get_entire_new();
        entireNew = JSON.parse(entireNewData.data);
        entireDropData = await get_entire_drop();
        entireDrop = JSON.parse(entireDropData.data);

        ETFDATA = await get_detail_data();
        items = JSON.parse(ETFDATA.data);

        priceDescData = await get_price_describe_data();
       
        increaseData = await get_data_by_order("increase");
        increase = JSON.parse(increaseData);

        decreaseData = await get_data_by_order("decrease");
        decrease = JSON.parse(decreaseData);

        newStockData = await get_data_by_order("new");
        newStock = JSON.parse(newStockData);

        dropStockData = await get_data_by_order("drop");
        dropStock = JSON.parse(dropStockData);

        telegramData = await get_telegram_data();
        telegramItems = JSON.parse(telegramData.data);
        top5 = telegramData.list;
        filteredTop5.push(top5[0]);
    });
</script>

<section>
    <Accordion>
        <AccordionItem>
            <span slot="header"> ✅ ETF가 새로 산 종목들</span>
            {#await entireNewData}
                "비중 늘어난 종목 기다리는 중"
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
                                            >{item["종목코드"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["종목명"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["보유량"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["보유금액"]}</TableBodyCell
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
                "비중 늘어난 종목 기다리는 중"
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
                                            >{item["종목코드"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["종목명"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["보유량"]}</TableBodyCell
                                        >
                                        <TableBodyCell
                                            >{item["보유금액"]}</TableBodyCell
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
</section>

<section>
    <div class="py-5">
    <Heading tag="h3">1. {name}의 보유 종목과 비중이에요.</Heading>

    <Tabs tabStyle="underline">
        <TabItem
            open
            title="상위 10개 종목 비중"
            activeClasses = 'p-4 font-bold text-red-500 border-red-600 border-b-2 rounded-t-lg dark:bg-gray-800 dark:text-primary-500'
            inactiveClasses = "p-4 text-black-500 bg-grey-600 dark:text-gray-400 bg-grey-700"
        >
            <div id="plot-top10">
                {#await top10Data}
                    "top10 data를 기다리는 중"
                {:then top10}
                    <Pie {top10} />
                {/await}
            </div>
        </TabItem>
        <TabItem
            title="보유종목 자세히 보기"
            activeClasses = 'p-4 font-bold text-red-500 border-red-600 border-b-2 rounded-t-lg dark:bg-gray-800 dark:text-primary-500'
            inactiveClasses = "p-4 text-black-500 bg-grey-600 dark:text-gray-400 bg-grey-700"
        >
            {#await ETFDATA}
                <p>waiting</p>
            {:then etf}

                    <div class="overflow-hidden hover:overflow-auto h-96">
                        <Table shadow>
                            <TableSearch
                                placeholder="회사명 검색"
                                hoverable={true}
                                bind:inputValue={searchTerm}
                            >
                                <TableHead>
                                    <TableHeadCell>종목명</TableHeadCell>
                                    <TableHeadCell>비중(%)</TableHeadCell>
                                    <TableHeadCell>평균 목표가</TableHeadCell>
                                    <TableHeadCell>리포트 제목</TableHeadCell>
                                    <TableHeadCell>의견</TableHeadCell>
                                    <TableHeadCell>게시일자</TableHeadCell>
                                    <TableHeadCell>증권사</TableHeadCell>
                                    <TableHeadCell>링크</TableHeadCell>
                                </TableHead>
                                <TableBody tableBodyClass="divide-y">
                                    {#each filteredItems as item}
                                        <TableBodyRow>
                                            <TableBodyCell
                                                >{item["종목명"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["비중"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["목표가"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "리포트 제목"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["의견"]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item[
                                                    "게시일자"
                                                ]}</TableBodyCell
                                            >
                                            <TableBodyCell
                                                >{item["증권사"]}</TableBodyCell
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
            {:catch error}
                {error}
            {/await}
        </TabItem>
    </Tabs>
</div>
</section>
<section>
    <div class = "py-5">
    <Heading tag="h3"
        >2. {name}의 상위 5개 종목과 관련된 이야기들이에요.</Heading
    >
    {#if Object.keys(telegramData).length == 0}
        <Alert color="blue">
            <Spinner class="me-3" size="8" color="alternative" />
            텔레그램 메세지를 모으고 있어요. 모두 모아오는 데에는 30초 정도 걸려요.
        </Alert>
    {:else}
        <Alert color="green">텔레그램 메세지를 모두 모아 왔어요.</Alert>

        <div class="flex gap-2">
            <Button color="alternative"
                >검색하고 싶은 종목<ChevronDownOutline
                    class="w-6 h-6 ms-2 text-black dark:text-white color"
                /></Button
            >
            <Dropdown class="overflow-y-auto px-3 pb-3 text-sm h-44">
                {#each telegramData.list as stock, index}
                    {#if index == 0}
                        <li
                            class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                            <Checkbox
                                checked
                                bind:group={filteredTop5}
                                value={stock}>{stock}</Checkbox
                            >
                        </li>
                    {:else}
                        <li
                            class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                            <Checkbox bind:group={filteredTop5} value={stock}
                                >{stock}</Checkbox
                            >
                        </li>
                    {/if}
                {/each}
            </Dropdown>

            <Button color="alternative"
                >확인하고 싶은 채널<ChevronDownOutline
                    class="w-6 h-6 ms-2 text-black dark:text-white"
                /></Button
            >
            <Dropdown class="overflow-y-auto px-3 pb-3 text-sm h-44">
                {#each channels as channel, index}
                    <li
                        class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
                    >
                        <Checkbox bind:group={filteredChannel} value={channel}
                            >{channel}</Checkbox
                        >
                    </li>
                {/each}
            </Dropdown>
        </div>

        <div>
            <div class="overflow-hidden hover:overflow-auto h-96">
                <Timeline class = 'px-4'>
                    {#each renderChannel as item}
                        <TimelineItem
                            title={item["채널명"]}
                            date={item["시간"]}
                        >
                            <p>
                                {item["종목명"]}에 관한 이야기에요. (링크 :<a
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
        </div>
    {/if}
    </div>
</section>
<section>
    <div class = "py-5">
    <Heading tag="h3">3. {name}의 최근 세 달 간 주가 추이에요.</Heading>
    <div class = 'py-4 flex justify-items-stretch gap-2'>
        {#await priceDescData}
        "분석데이터 기다리는 중"
        {:then desc}

        <!-- {#if type == 'Stock' & researchMsg['length'] != 0}
        <Alert class = 'py-4'color="dark" border>
            ✅ 평균 목표가({researchMsg['avgPrice']}원) 대비 현재 종가는 {priceDescData['target_ratio']}% 수준이에요.
            <P whitespace = "preline">
            ◾ 만일 {priceDescData['to_target']}% 상승한다면 증권사들의 평균 목표가에 도달해요.
            </P>
        </Alert>
        {/if} -->
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
            "price data를 기다리는 중"
            {:then price}
            <Line {price} />
            {/await}
        </div>
    </div>
</section>

<section>
    <div class = "py-5">
    <Heading tag="h3"
        >4. 최근 {name}에서 가장 비중이 늘어난 종목들이에요.</Heading
    >
    {#await increaseData}
        "비중 늘어난 종목 기다리는 중"
    {:then inc}
        <div class="py-4 overflow-hidden hover:overflow-auto max-h-96">
            <Table shadow>
                <TableHead>
                    <TableHeadCell>종목명</TableHeadCell>
                    <TableHeadCell>최근 비중(%)</TableHeadCell>
                    <TableHeadCell>일주일 전 비중(%)</TableHeadCell>
                    <TableHeadCell>차이(%p)</TableHeadCell>
                </TableHead>
                <TableBody tableBodyClass="divide-y">
                    {#each increase as item}
                        <TableBodyRow>
                            <TableBodyCell>{item["종목명"]}</TableBodyCell>
                            <TableBodyCell>{item["비중(기준일)"]}</TableBodyCell
                            >
                            <TableBodyCell>{item["비중(비교일)"]}</TableBodyCell
                            >
                            <TableBodyCell>{item["차이"]}</TableBodyCell>
                        </TableBodyRow>
                    {/each}
                </TableBody>
            </Table>
        </div>
    {/await}
</div>
</section>
<section>
<div class = "py-5">
    <Heading tag="h3"
        >5. 최근 {name}에서 가장 비중이 줄어든 종목들이에요.</Heading
    >
    {#await decreaseData}
        "비중 늘어난 종목 기다리는 중"
    {:then dec}
        <div class="py-4 overflow-hidden hover:overflow-auto max-h-96">
            <Table shadow>
                <TableHead>
                    <TableHeadCell>종목명</TableHeadCell>
                    <TableHeadCell>최근 비중(%)</TableHeadCell>
                    <TableHeadCell>일주일 전 비중(%)</TableHeadCell>
                    <TableHeadCell>차이(%p)</TableHeadCell>
                </TableHead>
                <TableBody tableBodyClass="divide-y">
                    {#each decrease as item}
                        <TableBodyRow>
                            <TableBodyCell>{item["종목명"]}</TableBodyCell>
                            <TableBodyCell>{item["비중(기준일)"]}</TableBodyCell
                            >
                            <TableBodyCell>{item["비중(비교일)"]}</TableBodyCell
                            >
                            <TableBodyCell>{item["차이"]}</TableBodyCell>
                        </TableBodyRow>
                    {/each}
                </TableBody>
            </Table>
        </div>
    {/await}
</div>
</section>
<section>
    <div class="py-5">
    <Heading tag="h3">6. 최근 {name}에서 새로 산 종목들이에요.</Heading>
    {#await newStockData}
        "새로 산 종목 기다리는 중"
    {:then ns}
        {#if newStock.length == 0}
            <Alert color="blue">
                <span class="font-medium">최근에 새로 산 종목은 없어요.</span>
            </Alert>
        {:else}
            <div class="py-4 overflow-hidden hover:overflow-auto max-h-96">
                <Table shadow>
                    <TableHead>
                        <TableHeadCell>종목명</TableHeadCell>
                        <TableHeadCell
                            >포트폴리오에 추가한 비중(%)</TableHeadCell
                        >
                    </TableHead>
                    <TableBody tableBodyClass="divide-y">
                        {#each newStock as item}
                            <TableBodyRow>
                                <TableBodyCell>{item["종목명"]}</TableBodyCell>
                                <TableBodyCell
                                    >{item["비중(기준일)"]}</TableBodyCell
                                >
                            </TableBodyRow>
                        {/each}
                    </TableBody>
                </Table>
            </div>
        {/if}
    {/await}
       </div>
</section>
<section>
    <div class="py-5">
    <Heading tag="h3">7. 최근 {name}에서 모두 판 종목들이에요.</Heading>
    {#await dropStockData}
        "비중을 모두 판 종목 기다리는 중"
    {:then drp}
        {#if dropStock.length == 0}
            <Alert color="blue">
                <span class="font-medium">최근에 모두 판 종목은 없어요.</span>
            </Alert>
        {:else}
            <div class="py-4 overflow-hidden hover:overflow-auto max-h-96">
                <Table shadow>
                    <TableHead>
                        <TableHeadCell>종목명</TableHeadCell>
                        <TableHeadCell
                            >포트폴리오에서 판매한 비중(%)</TableHeadCell
                        >
                    </TableHead>
                    <TableBody tableBodyClass="divide-y">
                        {#each dropStock as item}
                            <TableBodyRow>
                                <TableBodyCell>{item["종목명"]}</TableBodyCell>
                                <TableBodyCell
                                    >{item["비중(비교일)"]}</TableBodyCell
                                >
                            </TableBodyRow>
                        {/each}
                    </TableBody>
                </Table>
            </div>
        {/if}
    {/await}
    </div>
</section>

<style>
    #plot-top10 {
        margin: 1em;
        border-radius: 1em;
        padding-left: 5px;
        padding-right: 5px;
        padding-bottom: 5px;
        border: 1px solid lightgrey;
        max-width: 100%;
        align-self: center;
        align-items: center;
    }

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
