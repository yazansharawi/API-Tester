"""
Storage management for API Tester MCP Server
Handles saving/loading requests and history
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from config import config

class SimpleStorage:
    """Simple storage for requests and history"""
    
    def __init__(self):
        self.saved_requests: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        self.max_history = config.MAX_HISTORY
        
        # Load from files if enabled
        if config.SAVE_REQUESTS_TO_FILE:
            self._load_from_files()
    
    def save_request(self, name: str, request_data: Dict) -> None:
        """Save a request configuration for reuse"""
        self.saved_requests[name] = {
            **request_data,
            'saved_at': datetime.now().isoformat(),
            'id': name
        }
        
        if config.SAVE_REQUESTS_TO_FILE:
            self._save_requests_to_file()
    
    def get_request(self, name: str) -> Optional[Dict]:
        """Get a saved request by name"""
        return self.saved_requests.get(name)
    
    def list_saved_requests(self) -> List[str]:
        """List all saved request names"""
        return list(self.saved_requests.keys())
    
    def get_saved_requests_summary(self) -> List[Dict]:
        """Get summary of all saved requests"""
        return [
            {
                'name': name,
                'method': req.get('method', 'Unknown'),
                'url': req.get('url', 'Unknown'),
                'description': req.get('description', ''),
                'saved_at': req.get('saved_at', '')
            }
            for name, req in self.saved_requests.items()
        ]
    
    def delete_request(self, name: str) -> bool:
        """Delete a saved request"""
        if name in self.saved_requests:
            del self.saved_requests[name]
            
            if config.SAVE_REQUESTS_TO_FILE:
                self._save_requests_to_file()
            return True
        return False
    
    def update_request(self, name: str, request_data: Dict) -> bool:
        """Update an existing saved request"""
        if name in self.saved_requests:
            self.saved_requests[name].update({
                **request_data,
                'updated_at': datetime.now().isoformat()
            })
            
            if config.SAVE_REQUESTS_TO_FILE:
                self._save_requests_to_file()
            return True
        return False
    
    def add_to_history(self, request_data: Dict, response_data: Dict) -> None:
        """Add request/response to history"""
        entry = {
            'id': len(self.history) + 1,
            'timestamp': datetime.now().isoformat(),
            'request': self._clean_request_data(request_data),
            'response': self._clean_response_data(response_data)
        }
        
        self.history.insert(0, entry)
        
        # Keep only max_history items
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        if config.SAVE_REQUESTS_TO_FILE:
            self._save_history_to_file()
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent request history"""
        return self.history[:limit]
    
    def get_history_by_url(self, url: str, limit: int = 5) -> List[Dict]:
        """Get history filtered by URL"""
        filtered = [
            entry for entry in self.history 
            if entry['request'].get('url', '').lower() == url.lower()
        ]
        return filtered[:limit]
    
    def get_history_by_method(self, method: str, limit: int = 10) -> List[Dict]:
        """Get history filtered by HTTP method"""
        filtered = [
            entry for entry in self.history 
            if entry['request'].get('method', '').upper() == method.upper()
        ]
        return filtered[:limit]
    
    def clear_history(self) -> int:
        """Clear all history and return count of cleared items"""
        count = len(self.history)
        self.history = []
        
        if config.SAVE_REQUESTS_TO_FILE:
            self._save_history_to_file()
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if not self.history:
            return {
                'total_requests': 0,
                'saved_requests': len(self.saved_requests),
                'history_entries': 0,
                'success_rate': 0,
                'common_methods': {},
                'common_domains': {}
            }
        
        # Calculate success rate
        successful = sum(
            1 for entry in self.history 
            if entry['response'].get('status_code', 0) < 400
        )
        success_rate = (successful / len(self.history)) * 100 if self.history else 0
        
        # Count methods
        methods = {}
        domains = {}
        for entry in self.history:
            method = entry['request'].get('method', 'Unknown')
            methods[method] = methods.get(method, 0) + 1
            
            # Extract domain from URL
            url = entry['request'].get('url', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain:
                    domains[domain] = domains.get(domain, 0) + 1
            except:
                pass
        
        return {
            'total_requests': len(self.history),
            'saved_requests': len(self.saved_requests),
            'history_entries': len(self.history),
            'success_rate': round(success_rate, 1),
            'common_methods': dict(sorted(methods.items(), key=lambda x: x[1], reverse=True)[:5]),
            'common_domains': dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for backup"""
        return {
            'saved_requests': self.saved_requests,
            'history': self.history,
            'exported_at': datetime.now().isoformat(),
            'version': config.SERVER_VERSION
        }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup"""
        try:
            if 'saved_requests' in data:
                self.saved_requests.update(data['saved_requests'])
            
            if 'history' in data:
                # Merge histories, keeping most recent first
                existing_ids = {entry.get('id') for entry in self.history}
                new_entries = [
                    entry for entry in data['history'] 
                    if entry.get('id') not in existing_ids
                ]
                
                self.history = sorted(
                    self.history + new_entries,
                    key=lambda x: x.get('timestamp', ''),
                    reverse=True
                )[:self.max_history]
            
            if config.SAVE_REQUESTS_TO_FILE:
                self._save_requests_to_file()
                self._save_history_to_file()
            
            return True
        
        except Exception as e:
            print(f"Error importing data: {e}")
            return False
    
    def _clean_request_data(self, request_data: Dict) -> Dict:
        """Clean request data for storage"""
        return {
            'method': request_data.get('method'),
            'url': request_data.get('url'),
            'headers': request_data.get('headers', {}),
            'params': request_data.get('params', {}),
            'has_body': bool(request_data.get('body')),
            'timeout': request_data.get('timeout')
        }
    
    def _clean_response_data(self, response_data: Dict) -> Dict:
        """Clean response data for storage"""
        cleaned = {
            'status_code': response_data.get('status_code'),
            'status_text': response_data.get('status_text'),
            'size': response_data.get('size'),
            'time_ms': response_data.get('time_ms'),
            'content_type': response_data.get('headers', {}).get('content-type')
        }
        
        # Store error if present
        if 'error' in response_data:
            cleaned['error'] = response_data['error']
        
        return cleaned
    
    def _load_from_files(self):
        """Load data from files"""
        try:
            # Load saved requests
            if os.path.exists(config.REQUESTS_FILE_PATH):
                with open(config.REQUESTS_FILE_PATH, 'r') as f:
                    self.saved_requests = json.load(f)
            
            # Load history
            if os.path.exists(config.HISTORY_FILE_PATH):
                with open(config.HISTORY_FILE_PATH, 'r') as f:
                    self.history = json.load(f)
        
        except Exception as e:
            print(f"Error loading from files: {e}")
    
    def _save_requests_to_file(self):
        """Save requests to file"""
        try:
            with open(config.REQUESTS_FILE_PATH, 'w') as f:
                json.dump(self.saved_requests, f, indent=2)
        except Exception as e:
            print(f"Error saving requests to file: {e}")
    
    def _save_history_to_file(self):
        """Save history to file"""
        try:
            with open(config.HISTORY_FILE_PATH, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history to file: {e}")

# Global storage instance
storage = SimpleStorage()