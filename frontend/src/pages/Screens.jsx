import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Chip,
  IconButton,
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import api from '../services/api';

function Screens() {
  const [screens, setScreens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [newScreen, setNewScreen] = useState({
    name: '',
    image: null,
  });
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchScreens();
  }, []);

  const fetchScreens = async () => {
    try {
      const response = await api.get('/api/screens');
      setScreens(response.data);
    } catch (error) {
      console.error('Ekranlar yüklenirken hata oluştu:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setNewScreen({ name: '', image: null });
    setPreviewUrl('');
  };

  const handleChange = (e) => {
    setNewScreen({
      ...newScreen,
      [e.target.name]: e.target.value,
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setNewScreen({
        ...newScreen,
        image: file,
      });
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    if (!newScreen.image) {
      alert('Lütfen bir resim seçin');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('name', newScreen.name);
      formData.append('image', newScreen.image);

      await api.post('/api/screens', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      handleClose();
      fetchScreens();
    } catch (error) {
      console.error('Ekran eklenirken hata oluştu:', error);
      alert('Ekran eklenirken bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setUploading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Ekranlar</Typography>
        <Button variant="contained" onClick={handleClickOpen}>
          Yeni Ekran Ekle
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>İsim</TableCell>
              <TableCell>Görüntü</TableCell>
              <TableCell>Durum</TableCell>
              <TableCell>Son Kontrol</TableCell>
              <TableCell>Yanıt Süresi</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {screens.map((screen) => (
              <TableRow key={screen.id}>
                <TableCell>{screen.name}</TableCell>
                <TableCell>
                  <img
                    src={screen.image_url}
                    alt={screen.name}
                    style={{ maxWidth: '100px', maxHeight: '60px', objectFit: 'contain' }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={screen.status}
                    color={getStatusColor(screen.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(screen.last_check).toLocaleString()}
                </TableCell>
                <TableCell>{screen.response_time}ms</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Yeni Ekran Ekle</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Ekran Adı"
            type="text"
            fullWidth
            variant="outlined"
            value={newScreen.name}
            onChange={handleChange}
            sx={{ mb: 2 }}
          />
          <Box
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                borderColor: 'primary.main',
              },
            }}
            component="label"
          >
            <input
              type="file"
              accept="image/*"
              hidden
              onChange={handleImageChange}
            />
            {previewUrl ? (
              <Box sx={{ position: 'relative' }}>
                <img
                  src={previewUrl}
                  alt="Preview"
                  style={{ maxWidth: '100%', maxHeight: '200px', objectFit: 'contain' }}
                />
                <IconButton
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    bgcolor: 'rgba(255, 255, 255, 0.8)',
                    '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.9)' },
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setNewScreen({ ...newScreen, image: null });
                    setPreviewUrl('');
                  }}
                >
                  <CloudUploadIcon />
                </IconButton>
              </Box>
            ) : (
              <Box>
                <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body1" color="text.secondary">
                  Resim yüklemek için tıklayın veya sürükleyin
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  PNG, JPG veya JPEG (max. 5MB)
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>İptal</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!newScreen.image || uploading}
          >
            {uploading ? 'Yükleniyor...' : 'Ekle'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Screens; 