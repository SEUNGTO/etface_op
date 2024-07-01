<!-- Style -->

<script>
  import { onMount } from "svelte";
  import "./app.css";
  import ETF from "./contents/ETF.svelte";
  import Stock from "./contents/Stock.svelte";
  import { Heading, P } from "flowbite-svelte";
  import { Search } from "flowbite-svelte";
  import { Footer, FooterCopyright, FooterBrand } from "flowbite-svelte";
  import { Dropdown, DropdownItem } from "flowbite-svelte";

  let name = "";
  $: code = "";
  $: type = "";
  $: idx = {};
  let showComponent = false;

  $: keywords = nameList
    .filter((item) => item.toLowerCase().indexOf(name.toLowerCase()) !== -1)
    .slice(0, 5);

  const search = () => {
    idx = codeList.find((item) => item.Name === name);
    type = idx.Type;
    code = idx.Symbol;
    showComponent = true;
  };
  const initSearch = () => {
    showComponent = false;
  };

  const get_code_list = async () => {
    const url = `http://43.201.252.164/codelist`;
    const response = await fetch(url);
    const data = await response.json();
    return data;
  };
  let codeData = {};
  let codeList = {};
  let nameList = [];

  onMount(async () => {
    codeData = await get_code_list();
    codeList = JSON.parse(codeData);
    nameList = codeList.map((obj) => obj.Name);
  });
</script>

<main>
  <div class="container">
    <Heading
      tag="h1"
      class="mb-4"
      customSize="text-4xl font-extrabold  md:text-5xl lg:text-6xl"
      >ETF 관상가 😎 </Heading
    >

    <form
      id="search"
      on:submit|preventDefault={() => {
        search();
      }}
    >
      <Search
        placeholder="종목명을 입력해주세요(e.g. 삼성전자/TIGER 200 등)"
        class='hover:border-blue-600'
        bind:value={name}
        on:change={(e) => initSearch(e)}
        on:focus={(e) => {
          e;
        }}
      />
      <Dropdown classContainer="w-100" class="inline-flex items-left px-1 py-5">
        {#each keywords as matched_word}
          <DropdownItem
            on:click={() => {
              name = matched_word;
              search();
            }}
          >
            {matched_word}
          </DropdownItem>
        {/each}
      </Dropdown>
    </form>
    {#if type == "ETF" && showComponent == true}
      <ETF bind:code bind:name bind:type />
    {:else if type == "Stock" && showComponent == true}
      <Stock {code} {name} {type} />
    {:else if type == ""}
      종목명을 입력해주세요.
    {:else}
      종목명을 입력해주세요.
    {/if}
  </div>
</main>

<Footer footerType="logo">
  <div class="sm:flex sm:items-center sm:justify-between max-width:50%">
    <FooterBrand src="" alt="" name="ETF관상가" />
  </div>
  <hr class="my-6 border-gray-200 sm:mx-auto dark:border-gray-700 lg:my-8" />

  <div class="sm:flex sm:items-center sm:justify-between">
    <FooterCopyright href="/" by="ETF관상가" />
    <P color="text-grey-700 dark:text-grey-500" size="sm"
      >피드백/문의는 이메일(prof.etface@gmail.com)로 주세요.
    </P>
  </div>
</Footer>

<style>
  #search {
    padding: 10px;
    margin: 10px;
  }
</style>
