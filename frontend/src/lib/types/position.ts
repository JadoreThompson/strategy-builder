export interface Position {
  id: string;
  instrument: string;
  side: string;
  order_type: string;
  starting_amount: number;
  current_amount: number | null;
  price: number | null;
  limit_price: number | null;
  stop_price: number | null;
  tp_price: number | null;
  sl_price: number | null;
  realised_pnl: number | null;
  unrealised_pnl: number | null;
  status: string;
  created_at: string;
  close_price: number | null;
  closed_at: string | null;
}
