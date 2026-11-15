#!/usr/bin/env python3
"""Daily stock-site refresh helper.
plan:  python3 update.py plan PREV_DATA.json OUT_DIR LIST_PAGE1 [LIST_PAGE2 ...]
       -> OUT_DIR/base.json (items from list pages, carrying old details) and OUT_DIR/need.txt
          (item ids whose stock / last_modified_time changed or are new and need get_item).
merge: python3 update.py merge OUT_DIR RES1.json [RES2.json ...]
       -> OUT_DIR/data.json  (RES files: JSON arrays of {id,s,av,m,sh,ho,sr,pr} from get_item)
get_item fields: s=stock_on_hand, av=sum(locations[].location_asset_value),
m/sh/ho = location_stock_on_hand of "مخزن الرئيسي" / "المعرض" / "Head Office", sr=rate, pr=purchase_rate.
"""
import json, sys, os, datetime

SKIP = ('اجور', 'اشتراك')

def load_list(paths):
    out = []
    for p in paths:
        d = json.loads(open(p, encoding='utf-8').read())
        d = d.get('data', d)
        out += d['items']
    return out

def plan(prev_path, out_dir, pages):
    prev = {}
    if prev_path != '-' and os.path.exists(prev_path):
        prev = {i['id']: i for i in json.load(open(prev_path, encoding='utf-8')).get('items', [])}
    items, need = [], []
    for it in load_list(pages):
        if it.get('product_type') == 'service' or it['name'].startswith(SKIP):
            continue
        s = float(it.get('stock_on_hand') or 0)
        rec = {'id': it['item_id'], 'n': it['name'].replace('\ufffd', '').strip(), 's': s,
               'sr': float(it.get('rate') or 0), 'pr': float(it.get('purchase_rate') or 0),
               'lmt': it.get('last_modified_time', ''), 'm': 0, 'sh': 0, 'ho': 0, 'av': 0}
        old = prev.get(rec['id'])
        if s == 0:
            pass  # nothing in stock: no location detail needed
        elif old and old.get('s') == s and old.get('lmt') == rec['lmt'] and not old.get('err'):
            for k in ('m', 'sh', 'ho', 'av'):
                rec[k] = old.get(k, 0)
        else:
            need.append(rec['id'])
        items.append(rec)
    os.makedirs(out_dir, exist_ok=True)
    json.dump(items, open(os.path.join(out_dir, 'base.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(out_dir, 'need.txt'), 'w').write('\n'.join(need))
    print(f'items={len(items)} need_get_item={len(need)}')

def merge(out_dir, res_paths):
    items = json.load(open(os.path.join(out_dir, 'base.json'), encoding='utf-8'))
    res = {}
    for p in res_paths:
        for r in json.load(open(p, encoding='utf-8')):
            res[r['id']] = r
    need = [x for x in open(os.path.join(out_dir, 'need.txt')).read().split('\n') if x]
    miss = 0
    for it in items:
        r = res.get(it['id'])
        if r and not r.get('err'):
            for k in ('m', 'sh', 'ho', 'av'):
                it[k] = float(r.get(k) or 0)
            it['s'] = float(r.get('s', it['s']) or 0)
            if r.get('sr') is not None: it['sr'] = float(r['sr'] or 0)
            if r.get('pr') is not None: it['pr'] = float(r['pr'] or 0)
            it.pop('err', None)
        elif it['id'] in need:
            it['err'] = True; miss += 1
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    data = {'updated': now.strftime('%Y-%m-%dT%H:%M:%S+03:00'), 'items': items}
    json.dump(data, open(os.path.join(out_dir, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'data.json written: items={len(items)} missing_details={miss}')

if __name__ == '__main__':
    if sys.argv[1] == 'plan':
        plan(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        merge(sys.argv[2], sys.argv[3:])
