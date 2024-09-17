<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv46to47">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.6</literal> to <literal>4.7</literal>.
</para>
<xsl:template match="image" mode="conv46to47">
    <xsl:choose>
        <!-- nothing to do if already at 4.7 -->
        <xsl:when test="@schemaversion > 4.6">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.7">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv46to47"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv46to47">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </xsl:copy>
</xsl:template>

<!-- turn vmwareconfig into machine, ignore usb attribute -->
<xsl:template match="vmwareconfig" mode="conv46to47">
    <machine>
        <xsl:copy-of select="@*[not(local-name(.) = 'usb')]"/>
        <xsl:apply-templates mode="conv46to47"/>
    </machine>
</xsl:template>

<!-- turn xenconfig into machine -->
<xsl:template match="xenconfig" mode="conv46to47">
    <machine>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </machine>
</xsl:template>

<!-- turn vmwaredisk into vmdisk -->
<xsl:template match="vmwareconfig/vmwaredisk" mode="conv46to47">
    <vmdisk>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </vmdisk>
</xsl:template>

<!-- turn vmwarenic into vmnic -->
<xsl:template match="vmwareconfig/vmwarenic" mode="conv46to47">
    <vmnic>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </vmnic>
</xsl:template>

<!-- turn vmwarecdrom into vmdvd -->
<xsl:template match="vmwareconfig/vmwarecdrom" mode="conv46to47">
    <vmdvd>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </vmdvd>
</xsl:template>

<!-- turn xenbridge into vmnic -->
<xsl:template match="xenconfig/xenbridge" mode="conv46to47">
    <xsl:variable name="iface" select="@name"/>
    <vmnic>
        <xsl:attribute name="interface">
            <xsl:value-of select="$iface"/>
        </xsl:attribute>
        <xsl:copy-of select="@mac"/>
        <xsl:apply-templates mode="conv46to47"/>
    </vmnic>
</xsl:template>

<!-- turn xendisk into vmdisk -->
<xsl:template match="xenconfig/xendisk" mode="conv46to47">
    <vmdisk>
        <xsl:attribute name="controller">
            <xsl:text>ide</xsl:text>
        </xsl:attribute>
        <xsl:attribute name="id">
            <xsl:text>0</xsl:text>
        </xsl:attribute>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv46to47"/>
    </vmdisk>
</xsl:template>

<!-- turn format="iso" into installiso and format="usb" into installstick -->
<xsl:template match="type" mode="conv46to47">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'format')]"/>
        <xsl:choose>
            <xsl:when test="@format='iso'">
                <xsl:attribute name="installiso">
                    <xsl:text>true</xsl:text>
                </xsl:attribute>
            </xsl:when>
            <xsl:when test="@format='usb'">
                <xsl:attribute name="installstick">
                    <xsl:text>true</xsl:text>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="@format"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates mode="conv46to47"/>
    </type>
</xsl:template>

</xsl:stylesheet>
