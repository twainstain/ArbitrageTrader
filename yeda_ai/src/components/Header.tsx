import { AppBar, Box, Button, Container, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemButton, ListItemText } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import { useState } from 'react';

const Header = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { label: 'Home', id: 'home' },
    { label: 'Services', id: 'services' },
    { label: 'About', id: 'about' },
    { label: 'Contact', id: 'contact' },
  ];
  const navButtonStyle = {
    color: 'rgba(226,232,240,0.8)',
    transition: 'all 0.3s ease',
    fontSize: '0.9rem',
    fontWeight: 500,
    '&:hover': {
      color: '#64B4FF',
      background: 'transparent',
    }
  };

  const activeTabStyle = {
    position: 'relative',
    color: '#64B4FF !important',
    fontWeight: 600,
    '&::after': {
      content: '""',
      position: 'absolute',
      left: '50%',
      transform: 'translateX(-50%)',
      bottom: 0,
      width: '40%',
      height: '2px',
      background: '#64B4FF',
      borderRadius: '1px',
    }
  };

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <AppBar position="sticky" sx={{
      background: 'rgba(11, 20, 38, 0.95)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid rgba(100, 180, 255, 0.1)',
      boxShadow: 'none',
    }}>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 3 } }}>
        <Toolbar sx={{ justifyContent: 'space-between', minHeight: { xs: '56px', sm: '64px' } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{
              width: 52, height: 52,
              background: 'linear-gradient(135deg, #1E3A5F 0%, #0F2439 100%)',
              borderRadius: '14px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(59, 130, 246, 0.25), inset 0 1px 0 rgba(100, 180, 255, 0.1)',
              cursor: 'pointer',
              border: '1px solid rgba(100, 180, 255, 0.3)',
              position: 'relative',
              transition: 'all 0.3s ease',
              '&:hover': {
                boxShadow: '0 6px 25px rgba(59, 130, 246, 0.35), inset 0 1px 0 rgba(100, 180, 255, 0.15)',
                transform: 'translateY(-1px)',
              }
            }}>
              {/* Y-shaped connected dots icon */}
              <svg width="22" height="18" viewBox="0 0 20 16" style={{ marginBottom: 1 }}>
                <line x1="4" y1="3" x2="10" y2="9" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="16" y1="3" x2="10" y2="9" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="10" y1="9" x2="10" y2="15" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                <circle cx="4" cy="3" r="2" fill="#64B4FF"/>
                <circle cx="16" cy="3" r="2" fill="#64B4FF"/>
                <circle cx="10" cy="9" r="2.5" fill="#3B82F6"/>
                <circle cx="10" cy="15" r="2" fill="#64B4FF"/>
              </svg>
              <Typography sx={{
                background: 'linear-gradient(135deg, #64B4FF, #3B82F6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 700,
                fontSize: '0.6rem',
                lineHeight: 1,
                letterSpacing: '0.5px',
              }}>
                AI
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.8 }}>
              <Typography variant="h5" sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #CBD5E1 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.5rem',
                letterSpacing: '-0.5px',
                textShadow: '0 2px 10px rgba(255,255,255,0.1)',
              }}>
                Yeda
              </Typography>
              <Typography sx={{
                fontWeight: 600,
                background: 'linear-gradient(135deg, #64B4FF 0%, #3B82F6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: '1.1rem',
                letterSpacing: '1px',
              }}>
                AI
              </Typography>
            </Box>
          </Box>
          {/* Desktop Navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, alignItems: 'center' }}>
            <Button onClick={() => scrollToSection('home')} sx={{ ...navButtonStyle, ...activeTabStyle }}>Home</Button>
            <Button onClick={() => scrollToSection('services')} sx={navButtonStyle}>Services</Button>
            <Button onClick={() => scrollToSection('about')} sx={navButtonStyle}>About</Button>
            <Button onClick={() => scrollToSection('contact')} sx={{
              ...navButtonStyle,
              border: '1px solid rgba(100, 180, 255, 0.3)',
              borderRadius: '6px',
              px: 3,
              ml: 1,
              '&:hover': {
                border: '1px solid rgba(100, 180, 255, 0.5)',
                backgroundColor: 'rgba(100, 180, 255, 0.1)',
              }
            }}>Contact</Button>
          </Box>

          {/* Mobile Menu Button */}
          <IconButton
            sx={{ display: { xs: 'flex', md: 'none' }, color: '#64B4FF' }}
            onClick={() => setMobileOpen(true)}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </Container>

      {/* Mobile Drawer */}
      <Drawer
        anchor="right"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        PaperProps={{
          sx: {
            width: 280,
            background: 'linear-gradient(180deg, #0B1426 0%, #132238 100%)',
            borderLeft: '1px solid rgba(100, 180, 255, 0.1)',
          }
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <IconButton onClick={() => setMobileOpen(false)} sx={{ color: '#64B4FF' }}>
            <CloseIcon />
          </IconButton>
        </Box>
        <List sx={{ px: 2 }}>
          {navItems.map((item) => (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                onClick={() => {
                  scrollToSection(item.id);
                  setMobileOpen(false);
                }}
                sx={{
                  py: 2,
                  borderRadius: 2,
                  mb: 1,
                  '&:hover': { backgroundColor: 'rgba(100, 180, 255, 0.1)' },
                }}
              >
                <ListItemText
                  primary={item.label}
                  sx={{
                    '& .MuiListItemText-primary': {
                      color: '#E2E8F0',
                      fontWeight: 500,
                      fontSize: '1.1rem',
                    }
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
    </AppBar>
  );
};

export default Header;

