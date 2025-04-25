export interface IAction {
  navigate?: string | null;
  type?: string | null;
  click?: string | null;
  done?: boolean | null;
  scroll: boolean;
  target_visible: boolean;
  key?: string;
}
