import type { MarketQuote } from "@/types/chat";

export const MOCK_STOCK_QUOTES: Record<string, MarketQuote> = {
  AAPL: {
    symbol: "AAPL",
    price: 227.52,
    change24h: 1.84,
    currency: "USD",
    assetType: "stock",
  },
  TSLA: {
    symbol: "TSLA",
    price: 248.98,
    change24h: -2.31,
    currency: "USD",
    assetType: "stock",
  },
  MSFT: {
    symbol: "MSFT",
    price: 428.15,
    change24h: 0.67,
    currency: "USD",
    assetType: "stock",
  },
  NVDA: {
    symbol: "NVDA",
    price: 121.44,
    change24h: 3.12,
    currency: "USD",
    assetType: "stock",
  },
};

export const MOCK_CRYPTO_QUOTES: Record<string, MarketQuote> = {
  BTC: {
    symbol: "BTC",
    price: 64250.18,
    change24h: 2.45,
    currency: "USD",
    assetType: "crypto",
  },
  ETH: {
    symbol: "ETH",
    price: 3421.67,
    change24h: -1.08,
    currency: "USD",
    assetType: "crypto",
  },
  SOL: {
    symbol: "SOL",
    price: 148.92,
    change24h: 4.73,
    currency: "USD",
    assetType: "crypto",
  },
};

export const SUGGESTED_PROMPTS = [
  "What's the price of AAPL?",
  "How is Bitcoin doing today?",
  "Compare TSLA and NVDA briefly.",
  "Give me ETH's current price.",
] as const;
