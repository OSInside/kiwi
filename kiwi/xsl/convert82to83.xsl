<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv82to83">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv82to83"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>8.2</literal> to <literal>8.3</literal>.
</para>
<xsl:template match="image" mode="conv82to83">
    <xsl:choose>
        <!-- nothing to do if already at 8.3 -->
        <xsl:when test="@schemaversion > 8.2">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="8.3">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv82to83"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv82to83">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv82to83"/>
    </xsl:copy>
</xsl:template>

<!-- rename btrfs_root_is_snapshot attribute to btrfs_root_is_snapper_snapshot -->
<xsl:template match="type" mode="conv82to83">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'btrfs_root_is_snapshot')]"/>
        <xsl:if test="@btrfs_root_is_snapshot">
            <xsl:attribute name="btrfs_root_is_snapper_snapshot">
                <xsl:value-of select="@btrfs_root_is_snapshot"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates  mode="conv82to83"/>
    </type>
</xsl:template>

</xsl:stylesheet>
