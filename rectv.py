import re
import os
from typing import Dict, List

class M3UUpdater:
    def __init__(self):
        
        self.target_ids = ["70", "69", "68", "76", "74", "71", "72", "75", "67"]
        self.retv_channels = {}
        self.boniface_channels = {}
    
    def parse_m3u_file(self, file_path: str) -> Dict[str, Dict]:
        """M3U dosyasını parse eder ve kanal bilgilerini döndürür"""
        channels = {}
        
        if not os.path.exists(file_path):
            print(f"Dosya bulunamadı: {file_path}")
            return channels
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        
        blocks = content.split('#EXTINF:-1')
        
        for block in blocks[1:]:  
            if not block.strip():
                continue
                
            lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
            if len(lines) < 2:
                continue
                
            extinf_line = lines[0]
            
           
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', extinf_line)
            if not tvg_id_match:
                continue
                
            tvg_id = tvg_id_match.group(1)
            
            
            if tvg_id not in self.target_ids:
                continue
            
            
            url = ""
            user_agent = ""
            referrer = ""
            
            for line in lines[1:]:
                if line.startswith('http'):
                    url = line
                elif line.startswith('#EXTVLCOPT:http-user-agent='):
                    user_agent = line.replace('#EXTVLCOPT:http-user-agent=', '')
                elif line.startswith('#EXTVLCOPT:http-referrer='):
                    referrer = line.replace('#EXTVLCOPT:http-referrer=', '')
            
            channels[tvg_id] = {
                'extinf_line': extinf_line,
                'url': url,
                'user_agent': user_agent,
                'referrer': referrer,
                'full_block': block
            }
        
        return channels
    
    def load_channels(self, retv_path: str, boniface_path: str):
        """İki dosyayı yükler"""
        print("retv.m3u dosyası yükleniyor...")
        self.retv_channels = self.parse_m3u_file(retv_path)
        print(f"retv.m3u'dan {len(self.retv_channels)} hedef kanal yüklendi")
        
        print("boniface.m3u dosyası yükleniyor...")
        self.boniface_channels = self.parse_m3u_file(boniface_path)
        print(f"boniface.m3u'dan {len(self.boniface_channels)} hedef kanal yüklendi")
    
    def find_channels_to_update(self) -> List[str]:
        """Güncellenecek kanalları bulur"""
        channels_to_update = []
        
        for channel_id in self.target_ids:
            if channel_id in self.retv_channels and channel_id in self.boniface_channels:
                retv_channel = self.retv_channels[channel_id]
                boniface_channel = self.boniface_channels[channel_id]
                
                
                if (retv_channel['url'] != boniface_channel['url'] or
                    retv_channel['user_agent'] != boniface_channel['user_agent'] or
                    retv_channel['referrer'] != boniface_channel['referrer']):
                    channels_to_update.append(channel_id)
        
        return channels_to_update
    
    def update_boniface_file(self, boniface_path: str, backup: bool = True):
        """boniface.m3u dosyasını günceller"""
        if backup:
            backup_path = boniface_path + '.backup'
            if os.path.exists(boniface_path):
                with open(boniface_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Yedek dosya oluşturuldu: {backup_path}")
        
        
        channels_to_update = self.find_channels_to_update()
        
        if not channels_to_update:
            print("Güncellenecek kanal bulunamadı. Tüm kanallar zaten güncel.")
            return
        
        
        with open(boniface_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_count = 0
        
        for channel_id in channels_to_update:
            retv_channel = self.retv_channels[channel_id]
            boniface_channel = self.boniface_channels[channel_id]
            
            
            old_block = '#EXTINF:-1' + boniface_channel['full_block']
            
            
            new_lines = []
            old_lines = boniface_channel['full_block'].strip().split('\n')
            
            for line in old_lines:
                line = line.strip()
                if line.startswith('http'):
                    
                    new_lines.append(retv_channel['url'])
                elif line.startswith('#EXTVLCOPT:http-user-agent='):
                    
                    new_lines.append(f'#EXTVLCOPT:http-user-agent={retv_channel["user_agent"]}')
                elif line.startswith('#EXTVLCOPT:http-referrer='):
                    
                    new_lines.append(f'#EXTVLCOPT:http-referrer={retv_channel["referrer"]}')
                else:
                    
                    new_lines.append(line)
            
            new_block = '#EXTINF:-1' + '\n'.join(new_lines) + '\n'
            
            
            content = content.replace(old_block, new_block)
            updated_count += 1
            
            print(f"Güncellendi: ID {channel_id}")
            print(f"  Eski URL: {boniface_channel['url']}")
            print(f"  Yeni URL: {retv_channel['url']}")
            print(f"  User-Agent: {retv_channel['user_agent']}")
            print(f"  Referrer: {retv_channel['referrer']}")
            print()
        
        
        with open(boniface_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Toplam {updated_count} kanal güncellendi!")
    
    def show_status(self):
        """Hedef kanalların durumunu gösterir"""
        print(f"\n--- HEDEF KANALLAR ({len(self.target_ids)} adet) ---")
        
        for channel_id in self.target_ids:
            print(f"\nID: {channel_id}")
            
            retv_exists = channel_id in self.retv_channels
            boniface_exists = channel_id in self.boniface_channels
            
            print(f"  retv.m3u'da: {'✅' if retv_exists else '❌'}")
            print(f"  boniface.m3u'da: {'✅' if boniface_exists else '❌'}")
            
            if retv_exists and boniface_exists:
                retv_channel = self.retv_channels[channel_id]
                boniface_channel = self.boniface_channels[channel_id]
                
                url_same = retv_channel['url'] == boniface_channel['url']
                ua_same = retv_channel['user_agent'] == boniface_channel['user_agent']
                ref_same = retv_channel['referrer'] == boniface_channel['referrer']
                
                print(f"  URL aynı: {'✅' if url_same else '❌'}")
                print(f"  User-Agent aynı: {'✅' if ua_same else '❌'}")
                print(f"  Referrer aynı: {'✅' if ref_same else '❌'}")
                
                if not url_same:
                    print(f"    retv URL: {retv_channel['url']}")
                    print(f"    boniface URL: {boniface_channel['url']}")


def main():
    
    retv_path = "retv.m3u"
    boniface_path = "Kanallar/boniface.m3u"
    
    
    updater = M3UUpdater()
    
    print("🎯 Hedef ID'ler:", updater.target_ids)
    print()
    
    
    updater.load_channels(retv_path, boniface_path)
    
    
    updater.show_status()
    
    
    print("\n" + "="*50)
    print("🔄 GÜNCELLEMEYİ BAŞLATIYOR...")
    print("="*50)
    
    updater.update_boniface_file(boniface_path, backup=True)


if __name__ == "__main__":
    main()
